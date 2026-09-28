"""Model Service."""
from app.repositories.model_repository import ModelRepository
from app.database.models.model import Model
from app.database.models.evaluation import Evaluation
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.evaluation import (
    ComprehensiveComparisonResponse,
    ConfusionMatrix,
    MetricComparisonRow,
    ModelComparisonEntry,
)

class ModelService:
    def __init__(self, model_repo: ModelRepository = None):
        self.model_repo = model_repo or ModelRepository()
        self.dataset_repo = DatasetRepository()
        
    async def list_user_models(self, user_id: str):
        return await self.model_repo.list_by_user(user_id)
        
    async def register_model(self, user_id: str, name: str, model_type: str, description: str, is_default: bool = False):
        model = Model(
            user_id=user_id, 
            name=name, 
            model_type=model_type, 
            description=description, 
            is_default=is_default,
            status="pending"
        )
        return await self.model_repo.create(model)

    async def get_model(self, model_id: str, user_id: str, is_admin: bool = False):
        model = await self.model_repo.get_by_id(model_id)
        if not model:
            raise ResourceNotFoundError("Model", model_id)
        if model.user_id != user_id and not model.is_default and not is_admin:
            raise ResourceNotFoundError("Model", model_id)
        return model

    async def seed_default_models(self):
        defaults = [
            Model(user_id="system", name="Linear SVM Tabular Baseline", model_type="svm_linear", description="Built-in tabular baseline. The estimator is trained on the selected uploaded dataset.", is_default=True, status="active"),
            Model(user_id="system", name="RBF SVM Tabular Baseline", model_type="svm_rbf", description="Built-in non-linear tabular baseline. The estimator is trained on the selected uploaded dataset.", is_default=True, status="active"),
            Model(user_id="system", name="PennyLane VQC", model_type="vqc", description="Built-in variational quantum classifier trained on the selected uploaded dataset.", is_default=True, status="active"),
        ]
        results = []
        for d in defaults:
            # Upsert or ignore
            existing = await Model.find_one({"name": d.name, "user_id": "system", "is_default": True})
            if not existing:
                res = await self.model_repo.create(d)
                results.append(res)
            else:
                existing.model_type = d.model_type
                existing.description = d.description
                existing.is_default = True
                existing.status = "active"
                await self.model_repo.update(existing)
                results.append(existing)
        return results

    async def compare_selected_models(self, user_id: str, model_ids: list, model_version_ids: list, is_admin: bool = False):
        if model_version_ids:
            raise ValidationError("Compare saved trained model IDs; model-version comparison is not available.")
        selected_ids = list(dict.fromkeys(model_ids or []))
        if len(selected_ids) < 2:
            raise ValidationError("Select at least two trained models to compare.")

        entries = []
        for model_id in selected_ids:
            model = await self.get_model(model_id, user_id, is_admin)
            if model.status != "trained":
                raise ValidationError(f"Model '{model.name}' has not been trained on an uploaded dataset.")
            evaluation = await Evaluation.find(Evaluation.model_id == str(model.id)).sort(-Evaluation.created_at).first_or_none()
            if not evaluation:
                raise ValidationError(f"No evaluation record is available for model '{model.name}'.")
            metrics = evaluation.metrics_json or {}
            confusion = metrics.get("confusion_matrix", {})
            if isinstance(confusion, list) and len(confusion) == 4:
                tn, fp, fn, tp = confusion
                confusion = {"tn": tn, "fp": fp, "fn": fn, "tp": tp}
            config = model.configuration or {}
            dataset_version_id = config.get("dataset_version_id")
            version = await self.dataset_repo.get_version(dataset_version_id) if dataset_version_id else None
            entries.append(ModelComparisonEntry(
                model_id=str(model.id),
                model_name=model.name,
                model_type=model.model_type,
                version_tag=version.version_tag if version else "trained",
                feature_count=len(config.get("selected_features") or metrics.get("selected_features") or []),
                selected_features=config.get("selected_features") or metrics.get("selected_features") or [],
                accuracy=float(metrics.get("accuracy", evaluation.accuracy)),
                sensitivity=float(metrics.get("sensitivity", evaluation.recall)),
                specificity=float(metrics.get("specificity", 0.0)),
                precision=float(metrics.get("precision", evaluation.precision)),
                f1_score=float(metrics.get("f1_score", evaluation.f1_score)),
                balanced_accuracy=metrics.get("balanced_accuracy"),
                roc_auc=evaluation.roc_auc,
                confusion_matrix=ConfusionMatrix(
                    true_positive=int(confusion.get("tp", 0)),
                    true_negative=int(confusion.get("tn", 0)),
                    false_positive=int(confusion.get("fp", 0)),
                    false_negative=int(confusion.get("fn", 0)),
                ),
                training_duration_sec=metrics.get("training_duration_seconds"),
                quantum_details={"model_type": model.model_type} if model.model_type == "vqc" else None,
            ))

        definitions = [
            ("accuracy", "Accuracy", True),
            ("balanced_accuracy", "Balanced accuracy", True),
            ("sensitivity", "Sensitivity", True),
            ("specificity", "Specificity", True),
            ("precision", "Precision", True),
            ("f1_score", "F1 score", True),
            ("roc_auc", "ROC AUC", True),
            ("training_duration_sec", "Training duration (seconds)", False),
        ]
        rows = []
        winners: Dict[str, str] = {}
        for key, label, higher_is_better in definitions:
            values = {entry.model_name: getattr(entry, key) for entry in entries if getattr(entry, key) is not None}
            best = (max if higher_is_better else min)(values, key=values.get) if values else "Unavailable"
            if values:
                winners[label] = best
            rows.append(MetricComparisonRow(
                metric_key=key, display_name=label, higher_is_better=higher_is_better,
                values=values, best_model=best,
            ))

        classical = [entry.accuracy for entry in entries if entry.model_type != "vqc"]
        quantum = [entry.accuracy for entry in entries if entry.model_type == "vqc"]
        insights = {
            "interpretation": "Descriptive comparison of the selected runs; it is not a statistical significance test.",
            "classical_mean_accuracy": sum(classical) / len(classical) if classical else None,
            "quantum_mean_accuracy": sum(quantum) / len(quantum) if quantum else None,
            "dataset_versions": sorted({str((model.configuration or {}).get("dataset_version_id", "")) for model in [await self.get_model(model_id, user_id, is_admin) for model_id in selected_ids]}),
        }
        markdown = ["| Model | Type | Accuracy | Sensitivity | Specificity | F1 | ROC AUC |", "|---|---|---:|---:|---:|---:|---:|"]
        for entry in entries:
            auc = f"{entry.roc_auc:.4f}" if entry.roc_auc is not None else "N/A"
            markdown.append(f"| {entry.model_name} | {entry.model_type} | {entry.accuracy:.4f} | {entry.sensitivity:.4f} | {entry.specificity:.4f} | {entry.f1_score:.4f} | {auc} |")
        return ComprehensiveComparisonResponse(
            models_compared=entries,
            comparison_matrix=rows,
            category_winners=winners,
            cml_vs_qml_insights=insights,
            markdown_table="\n".join(markdown),
            executive_summary=f"Compared {len(entries)} trained models using their saved held-out test metrics.",
        )
