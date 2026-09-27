"""Model registry service managing architectures, versions, weights, and multi-model comparative evaluation."""

from typing import Any, Dict, List, Optional
from app.core.exceptions import CrossUserAccessError, ResourceNotFoundError, ValidationError
from app.database.models.model import Model, ModelConfig, ModelVersion
from app.ml.loader import pretrained_model_loader
from app.repositories.model_repository import ModelRepository
from app.schemas.evaluation import (
    ComprehensiveComparisonResponse,
    ConfusionMatrix,
    MetricComparisonRow,
    ModelComparisonEntry,
)


class ModelService:
    """Service managing model registration, hyperparameter configurations, trained versions, and multi-model benchmarking."""

    def __init__(self, model_repo: ModelRepository):
        self.model_repo = model_repo

    async def register_model(
        self,
        user_id: Optional[str],
        name: str,
        model_type: str,
        description: Optional[str] = None,
        is_default: bool = False,
    ) -> Model:
        """Register a new model archetype (svm_linear, svm_rbf, vqc)."""
        valid_types = {"svm_linear", "svm_rbf", "vqc"}
        if model_type not in valid_types:
            raise ValidationError(f"Invalid model_type '{model_type}'. Supported types: {list(valid_types)}")

        model = Model(
            user_id=user_id,
            name=name,
            model_type=model_type,
            description=description,
            is_default=is_default,
        )
        return await self.model_repo.create(model)

    async def get_model(self, model_id: str, user_id: str, is_admin: bool = False) -> Model:
        """Fetch model by ID, allowing access if user owns it or if it is a system default model."""
        model = await self.model_repo.get_by_id(model_id)
        if not model:
            raise ResourceNotFoundError(resource_type="Model", resource_id=model_id)
        if not is_admin and not model.is_default and model.user_id != user_id:
            raise CrossUserAccessError(resource_type="Model", resource_id=model_id)
        return model

    async def list_user_models(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Model]:
        """List models accessible to user (their own custom models + system-wide default models)."""
        return await self.model_repo.list_by_user(user_id, skip=skip, limit=limit)

    async def get_model_version(self, version_id: str, user_id: str, is_admin: bool = False) -> ModelVersion:
        """Fetch specific trained model version, permitting default models to all users."""
        version = await self.model_repo.get_version_by_id(version_id)
        if not version:
            raise ResourceNotFoundError(resource_type="ModelVersion", resource_id=version_id)
        if not is_admin and not version.is_default and version.user_id != user_id:
            raise CrossUserAccessError(resource_type="ModelVersion", resource_id=version_id)
        return version

    async def seed_default_models(self) -> List[Model]:
        """Seed the pre-trained repository models into the registry with their complete evaluation metrics."""
        available_models = pretrained_model_loader.list_available_models()
        seeded = []

        for m_meta in available_models:
            existing = await self.model_repo.get_by_name(m_meta["model_name"])
            if not existing:
                model = Model(
                    user_id=None,
                    name=m_meta["model_name"],
                    model_type=m_meta["model_type"],
                    description=f"Pre-trained model from {m_meta.get('source_experiment', 'research')}",
                    is_default=True,
                )
                created_model = await self.model_repo.create(model)

                metrics_payload = m_meta.get("metrics", {})
                metrics_payload["feature_count"] = m_meta.get("feature_count", 4)
                metrics_payload["selected_features"] = m_meta.get("selected_features", [])
                metrics_payload["framework"] = m_meta.get("framework", "scikit-learn")
                if "quantum_device" in m_meta:
                    metrics_payload["quantum_device"] = m_meta["quantum_device"]
                if "noise_channels" in m_meta:
                    metrics_payload["noise_channels"] = m_meta["noise_channels"]

                version = ModelVersion(
                    model_id=created_model.id,
                    user_id=None,
                    version_tag="v1.0.0-pretrained",
                    metrics=metrics_payload,
                    status="active",
                    is_default=True,
                )
                await self.model_repo.create_version(version)
                seeded.append(created_model)
            else:
                seeded.append(existing)

        return seeded

    async def compare_selected_models(
        self,
        user_id: str,
        model_ids: Optional[List[str]] = None,
        model_version_ids: Optional[List[str]] = None,
        is_admin: bool = False,
    ) -> ComprehensiveComparisonResponse:
        """Compare two or more selected models across ALL clinical evaluation metrics."""
        # 1. Ensure default models are seeded
        await self.seed_default_models()

        entries: List[ModelComparisonEntry] = []
        target_models: List[Model] = []

        if model_ids:
            for m_id in model_ids:
                m = await self.get_model(m_id, user_id, is_admin)
                target_models.append(m)
        elif model_version_ids:
            for mv_id in model_version_ids:
                mv = await self.get_model_version(mv_id, user_id, is_admin)
                m = await self.get_model(mv.model_id, user_id, is_admin)
                target_models.append(m)

        if len(target_models) < 2:
            raise ValidationError("At least two distinct models must be selected for comparison.")

        # 2. Extract metrics for each model
        for m in target_models:
            # Grab latest version
            versions = await self.model_repo.session.execute(
                self.model_repo.session.query(ModelVersion).filter(ModelVersion.model_id == m.id)
            ) if hasattr(self.model_repo.session, "query") else None

            # Fallback query
            from sqlalchemy import select
            v_res = await self.model_repo.session.execute(
                select(ModelVersion).where(ModelVersion.model_id == m.id).order_by(ModelVersion.created_at.desc())
            )
            version = v_res.scalars().first()
            raw_metrics = version.metrics if (version and version.metrics) else {}

            cm_dict = raw_metrics.get("confusion_matrix", {})
            cm = ConfusionMatrix(
                true_positive=int(cm_dict.get("true_positive", cm_dict.get("tp", 0))),
                true_negative=int(cm_dict.get("true_negative", cm_dict.get("tn", 0))),
                false_positive=int(cm_dict.get("false_positive", cm_dict.get("fp", 0))),
                false_negative=int(cm_dict.get("false_negative", cm_dict.get("fn", 0))),
            )

            quantum_details = None
            if m.model_type == "vqc":
                quantum_details = {
                    "quantum_device": raw_metrics.get("quantum_device", "default.qubit"),
                    "noise_channels": raw_metrics.get("noise_channels", None),
                    "n_qubits": raw_metrics.get("feature_count", 4),
                }

            entry = ModelComparisonEntry(
                model_id=m.id,
                model_name=m.name,
                model_type=m.model_type,
                version_tag=version.version_tag if version else "v1.0",
                feature_count=raw_metrics.get("feature_count", 4),
                selected_features=raw_metrics.get("selected_features", []),
                accuracy=float(raw_metrics.get("accuracy", 0.0)),
                sensitivity=float(raw_metrics.get("sensitivity", 0.0)),
                specificity=float(raw_metrics.get("specificity", 0.0)),
                precision=float(raw_metrics.get("precision", 0.0)),
                f1_score=float(raw_metrics.get("f1_score", 0.0)),
                balanced_accuracy=float(raw_metrics.get("balanced_accuracy", raw_metrics.get("accuracy", 0.0))),
                roc_auc=float(raw_metrics.get("roc_auc", 0.5)),
                confusion_matrix=cm,
                training_duration_sec=raw_metrics.get("training_duration_seconds", None),
                quantum_details=quantum_details,
            )
            entries.append(entry)

        # 3. Build side-by-side metric comparison matrix
        metric_definitions = [
            ("accuracy", "Overall Accuracy", True),
            ("balanced_accuracy", "Balanced Accuracy", True),
            ("sensitivity", "Sensitivity (Recall / True Positive Rate)", True),
            ("specificity", "Specificity (True Negative Rate)", True),
            ("precision", "Positive Predictive Value (Precision)", True),
            ("f1_score", "F1-Score (Harmonic Mean)", True),
            ("roc_auc", "Area Under ROC Curve (ROC-AUC)", True),
            ("training_duration_sec", "Training Duration (Seconds)", False),
        ]

        matrix_rows: List[MetricComparisonRow] = []
        winners: Dict[str, str] = {}

        for m_key, disp_name, higher_is_better in metric_definitions:
            val_map = {}
            for e in entries:
                val = getattr(e, m_key, None)
                if val is not None:
                    val_map[e.model_name] = round(val, 4) if isinstance(val, float) else val

            if val_map:
                if higher_is_better:
                    best_m = max(val_map.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else -1)[0]
                else:
                    best_m = min(val_map.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 9999)[0]
                
                winners[disp_name] = f"{best_m} ({val_map[best_m]})"
                matrix_rows.append(
                    MetricComparisonRow(
                        metric_key=m_key,
                        display_name=disp_name,
                        higher_is_better=higher_is_better,
                        values=val_map,
                        best_model=best_m,
                    )
                )

        # 4. Generate CML vs QML comparative insights
        cml_entries = [e for e in entries if e.model_type in ["svm_linear", "svm_rbf"]]
        qml_entries = [e for e in entries if e.model_type == "vqc"]
        cml_vs_qml_insights = {
            "classical_models_count": len(cml_entries),
            "quantum_models_count": len(qml_entries),
            "classical_mean_accuracy": round(sum(e.accuracy for e in cml_entries) / len(cml_entries), 4) if cml_entries else None,
            "quantum_mean_accuracy": round(sum(e.accuracy for e in qml_entries) / len(qml_entries), 4) if qml_entries else None,
            "classical_mean_specificity": round(sum(e.specificity for e in cml_entries) / len(cml_entries), 4) if cml_entries else None,
            "quantum_mean_specificity": round(sum(e.specificity for e in qml_entries) / len(qml_entries), 4) if qml_entries else None,
        }

        # 5. Build Markdown Comparison Table
        md_lines = [
            "# Comprehensive Multi-Model Comparative Evaluation",
            "",
            "| Evaluation Metric | " + " | ".join(e.model_name for e in entries) + " | Best Performer |",
            "| :--- | " + " | ".join(":---:" for _ in entries) + " | :--- |",
        ]
        for row in matrix_rows:
            vals = [str(row.values.get(e.model_name, "N/A")) for e in entries]
            md_lines.append(f"| **{row.display_name}** | " + " | ".join(vals) + f" | **{row.best_model}** |")

        md_lines.extend([
            "",
            "### Confusion Matrix Breakdown",
            "| Model | True Positive (TP) | False Positive (FP) | True Negative (TN) | False Negative (FN) |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ])
        for e in entries:
            cm = e.confusion_matrix
            md_lines.append(f"| **{e.model_name}** | {cm.true_positive} | {cm.false_positive} | {cm.true_negative} | {cm.false_negative} |")

        markdown_table = "\n".join(md_lines)

        summary_text = (
            f"Compared {len(entries)} models across 8 clinical evaluation metrics. "
            f"Top accuracy achieved by {winners.get('Overall Accuracy', 'N/A')}, "
            f"while top sensitivity (critical for cancer screening) was {winners.get('Sensitivity (Recall / True Positive Rate)', 'N/A')}."
        )

        return ComprehensiveComparisonResponse(
            models_compared=entries,
            comparison_matrix=matrix_rows,
            category_winners=winners,
            cml_vs_qml_insights=cml_vs_qml_insights,
            markdown_table=markdown_table,
            executive_summary=summary_text,
        )
