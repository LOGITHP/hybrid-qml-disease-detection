"""Evaluation metrics and comprehensive multi-model comparison endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics import roc_curve, precision_recall_curve, auc, confusion_matrix, accuracy_score, recall_score, precision_score, f1_score

from app.core.dependencies import get_current_user
from app.database.models.user import User
from app.database.models.training import TrainingRun
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.experiment import Experiment

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Diagnostics"])


@router.get("/{training_run_id}")
async def get_evaluation_context(
    training_run_id: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieve full evaluation context and core metrics for a specific training run."""
    run = await TrainingRun.get(training_run_id)
    if not run or run.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Training Run not found")

    metrics = run.metrics or {}
    
    # Try to fetch dataset info
    dataset_name = "Unknown Dataset"
    if run.dataset_version_id:
        import uuid
        try:
            version_id = uuid.UUID(run.dataset_version_id) if '-' in run.dataset_version_id else run.dataset_version_id
            version = await DatasetVersion.get(version_id)
            if version:
                dataset = await Dataset.get(version.dataset_id)
                if dataset:
                    dataset_name = dataset.name
        except Exception:
            pass

    return {
        "training_run_id": str(run.id),
        "dataset_id": run.dataset_version_id,
        "dataset_name": dataset_name,
        "preprocessing_run_id": run.preprocessing_run_id,
        "feature_selection_run_id": run.feature_selection_run_id,
        "learning_type": run.learning_type,
        "model_type": run.model_type,
        "evaluation_set": metrics.get("evaluation_partition", "held-out test"),
        "target_column": metrics.get("target_column", "Unknown"),
        "selected_feature_count": len(run.feature_config.get("selected_features", [])),
        "sample_count": len(metrics.get("y_true_test", [])) if "y_true_test" in metrics else 0,
        "metrics": {
            "accuracy": metrics.get("accuracy", 0.0),
            "balanced_accuracy": metrics.get("balanced_accuracy", 0.0),
            "sensitivity": metrics.get("sensitivity", 0.0),
            "specificity": metrics.get("specificity", 0.0),
            "precision": metrics.get("precision", 0.0),
            "f1_score": metrics.get("f1_score", 0.0),
            "roc_auc": metrics.get("roc_auc", 0.0),
            "generalization": metrics.get("generalization")
        },
        "confusion_matrix": metrics.get("confusion_matrix", {"tp": 0, "tn": 0, "fp": 0, "fn": 0}),
        "computational": {
            "training_time": metrics.get("training_duration_seconds"),
            "inference_time": metrics.get("inference_duration_ms"),
            "trainable_parameters": run.model_parameters.get("trainable_parameters") if run.model_parameters else None
        },
        "quantum": run.qml_config if run.learning_type == "QML" else None,
        "y_true": metrics.get("y_true_test", []),
        "y_prob": metrics.get("y_prob_test", [])
    }


@router.post("/compare")
async def compare_training_runs(
    payload: Dict[str, List[str]],
    current_user: User = Depends(get_current_user)
):
    """Compare multiple models directly based on their training runs."""
    run_ids = payload.get("training_run_ids", [])
    if len(run_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least two training_run_ids to compare.")

    runs = []
    for rid in run_ids:
        r = await TrainingRun.get(rid)
        if r and r.user_id == str(current_user.id):
            runs.append(r)

    if len(runs) < 2:
        raise HTTPException(status_code=404, detail="Could not find sufficient valid training runs to compare.")

    comparison_results = []
    for run in runs:
        metrics = run.metrics or {}
        comparison_results.append({
            "training_run_id": str(run.id),
            "model_type": run.model_type,
            "learning_type": run.learning_type,
            "metrics": {
                "accuracy": metrics.get("accuracy", 0.0),
                "balanced_accuracy": metrics.get("balanced_accuracy", 0.0),
                "sensitivity": metrics.get("sensitivity", 0.0),
                "specificity": metrics.get("specificity", 0.0),
                "precision": metrics.get("precision", 0.0),
                "f1_score": metrics.get("f1_score", 0.0),
                "roc_auc": metrics.get("roc_auc", 0.0),
            },
            "training_duration_seconds": metrics.get("training_duration_seconds")
        })

    return {"models_compared": comparison_results}
