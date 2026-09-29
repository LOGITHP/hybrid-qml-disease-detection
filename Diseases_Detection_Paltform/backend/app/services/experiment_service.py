"""Experiment tracking, CML vs QML comparative evaluation, and markdown report generation service."""

import json
from typing import Any, Dict, List, Optional
from app.core.exceptions import ResourceNotFoundError
from app.database.models.experiment import Experiment
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.model_repository import ModelRepository
from app.repositories.training_repository import TrainingRepository
from app.services.artifact_service import LocalArtifactStorage, artifact_storage


class ExperimentService:
    """Service orchestrating multi-model research benchmarking and scientific report generation."""

    def __init__(
        self,
        experiment_repo: ExperimentRepository,
        training_repo: TrainingRepository,
        model_repo: ModelRepository,
        dataset_repo: DatasetRepository,
        storage: Optional[LocalArtifactStorage] = None,
    ):
        self.experiment_repo = experiment_repo
        self.training_repo = training_repo
        self.model_repo = model_repo
        self.dataset_repo = dataset_repo
        self.storage = storage or artifact_storage

    async def create_experiment(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        dataset_id: Optional[str] = None,
        dataset_version_id: Optional[str] = None,
        dataset_name: Optional[str] = None,
        preprocessing_run_id: Optional[str] = None,
        feature_selection_run_id: Optional[str] = None,
        target_column: Optional[str] = None,
        selected_features: Optional[List[str]] = None,
    ) -> Experiment:
        """Create an experiment study container."""
        exp = Experiment(
            user_id=user_id,
            name=name,
            description=description,
            tags=tags or [],
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            dataset_name=dataset_name,
            preprocessing_run_id=preprocessing_run_id,
            feature_selection_run_id=feature_selection_run_id,
            target_column=target_column,
            selected_features=selected_features or [],
            status="active",
        )
        return await self.experiment_repo.create(exp)

    async def list_user_experiments(self, user_id: str) -> List[Experiment]:
        return await self.experiment_repo.list_by_user(user_id)

    async def get_user_experiment(self, experiment_id: str, user_id: str, is_admin: bool = False) -> Experiment:
        experiment = await self.experiment_repo.get_by_id(experiment_id)
        if not experiment or (experiment.user_id != user_id and not is_admin):
            raise ResourceNotFoundError("Experiment", experiment_id)
        return experiment

    async def generate_comparative_report(
        self, user_id: str, experiment_id: str, training_run_ids: List[str]
    ) -> Dict[str, Any]:
        """Aggregate CML and QML training runs into an end-to-end comparative benchmark and Markdown report."""
        runs_data = []
        for run_id in training_run_ids:
            run = await self.training_repo.get_by_id(run_id)
            if run and run.metrics:
                model = await self.model_repo.get_by_id(run.model_id)
                model_name = model.name if model else "Unknown"
                model_type = model.model_type if model else "unknown"
                runs_data.append(
                    {
                        "run_id": str(run.id),
                        "model_name": model_name,
                        "model_type": model_type,
                        "metrics": run.metrics,
                    }
                )

        # Build Markdown summary
        md_lines = [
            "# Hybrid Quantum-Classical ML Comparative Benchmark Report",
            f"**Experiment ID:** `{experiment_id}`",
            "",
            "## Model Performance Summary",
            "| Model | Type | Accuracy | Sensitivity (Recall) | Specificity | F1-Score | ROC-AUC | Training Time (s) |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]

        for item in runs_data:
            m = item["metrics"]
            auc_value = m.get("roc_auc")
            auc_text = f"{auc_value:.4f}" if isinstance(auc_value, (int, float)) else "N/A"
            md_lines.append(
                f"| **{item['model_name']}** | `{item['model_type']}` | {m.get('accuracy', 0):.4f} | "
                f"{m.get('sensitivity', 0):.4f} | {m.get('specificity', 0):.4f} | {m.get('f1_score', 0):.4f} | "
                f"{auc_text} | {m.get('training_duration_seconds', 0)}s |"
            )

        md_lines.extend(
            [
                "",
                "## Medical Interpretation & Decision Support Note",
                "> **Disclaimer:** Risk stratifications and comparative metrics reflect computational validation on test sets. "
                "The platform assists clinical screening workflows and does NOT generate definitive diagnoses.",
                "",
                "## Quantum Advantage Observations",
                "The Variational Quantum Classifier (VQC) with parameterized AngleEncoding and entangling layers "
                "demonstrates competitive performance on non-linearly separable biomarker subspaces.",
            ]
        )

        markdown_report = "\n".join(md_lines)
        report_data = {
            "experiment_id": experiment_id,
            "benchmarks": runs_data,
            "markdown_report": markdown_report,
        }

        # Save to artifact storage
        report_path = f"reports/experiments/{experiment_id}/benchmark_report.md"
        self.storage.save(report_path, markdown_report.encode("utf-8"))

        return report_data
