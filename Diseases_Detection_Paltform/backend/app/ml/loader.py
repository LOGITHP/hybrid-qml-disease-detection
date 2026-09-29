"""Loader utility for importing existing trained models into the backend application."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
from pennylane import numpy as pnp
from app.core.exceptions import ResourceNotFoundError
from app.interfaces.model import IModel
from app.ml.classical.svm.linear import SVMLinearModel
from app.ml.classical.svm.rbf import SVMRBFModel
from app.ml.quantum.vqc.model import VariationalQuantumClassifier

PRETRAINED_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "pretrained"

def _get_project_root() -> Path:
    """Find the checkout root by its experiment folder, with a safe container fallback."""
    loader_path = Path(__file__).resolve()
    for parent in loader_path.parents:
        if (parent / "Experimental_ML" / "Lung_Cancer").is_dir():
            return parent
    parents = loader_path.parents
    return parents[min(2, len(parents) - 1)]


class PretrainedModelLoader:
    """Manages loading of existing pre-trained CML and QML models into backend IModel instances."""

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or PRETRAINED_DIR
        self.metadata_path = self.models_dir / "metadata.json"

    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all pre-trained models with their feature requirements and architectures."""
        if not self.metadata_path.exists():
            return []
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("models", [])

    @staticmethod
    def _normalize_experiment_metrics(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Normalize the experiment result JSON variants to the model API metric shape."""
        if not row:
            return {}
        source = row.get("metrics") if isinstance(row.get("metrics"), dict) else row
        def first(*keys):
            return next((source[key] for key in keys if source.get(key) is not None), None)
        confusion = (
            row.get("confusion_matrix") or row.get("Confusion Matrix")
            or source.get("confusion_matrix") or source.get("Confusion Matrix") or {}
        )
        if confusion and "True Positive" in confusion:
            confusion = {
                "true_positive": confusion.get("True Positive"),
                "true_negative": confusion.get("True Negative"),
                "false_positive": confusion.get("False Positive"),
                "false_negative": confusion.get("False Negative"),
            }
        metrics = {
            "accuracy": first("accuracy", "Accuracy"),
            "balanced_accuracy": first("balanced_accuracy", "Balanced Accuracy"),
            "sensitivity": first("sensitivity", "Sensitivity", "Sensitivity (Recall)"),
            "specificity": first("specificity", "Specificity"),
            "precision": first("precision", "Precision"),
            "f1_score": first("f1_score", "F1-Score", "F1-score"),
            "roc_auc": first("roc_auc", "ROC-AUC"),
            "training_duration_seconds": first("training_duration_seconds", "training_time_seconds"),
            "confusion_matrix": confusion,
        }
        if row.get("test_samples") is not None:
            metrics["test_samples"] = int(row["test_samples"])
        elif confusion:
            metrics["test_samples"] = int(sum(value for value in confusion.values() if isinstance(value, (int, float))))
        return {key: value for key, value in metrics.items() if value is not None}

    def _resolve_model_file(self, filename: str) -> Path:
        path = Path(filename)
        if path.is_absolute():
            return path
        experiment_path = PROJECT_ROOT / path
        if experiment_path.is_file():
            return experiment_path
        if path.parts[:2] == ("Experimental_ML", "Lung_Cancer"):
            mounted_experiment_path = EXPERIMENT_ROOT.joinpath(*path.parts[2:])
            if mounted_experiment_path.is_file():
                return mounted_experiment_path
        return self.models_dir / path

    def load_classical_svm(self, model_filename: str) -> Any:
        """Load pre-trained Scikit-Learn SVM (.joblib)."""
        file_path = self._resolve_model_file(model_filename)
        if not file_path.exists():
            raise ResourceNotFoundError("PretrainedModelFile", str(file_path))
        return joblib.load(file_path)

    def load_vqc_model(
        self,
        weights_filename: str,
        bias_filename: str,
        n_qubits: int = 4,
        n_layers: int = 2,
        is_noisy: bool = False,
        noise_params: Optional[Dict[str, float]] = None,
    ) -> VariationalQuantumClassifier:
        """Load pre-trained PennyLane VQC variational weights and bias."""
        w_path = self._resolve_model_file(weights_filename)
        b_path = self._resolve_model_file(bias_filename)

        if not w_path.exists() or not b_path.exists():
            raise ResourceNotFoundError("VQCWeightsFile", f"{w_path} or {b_path}")

        weights = np.load(w_path)
        bias = np.load(b_path)

        vqc = VariationalQuantumClassifier(
            n_qubits=n_qubits,
            n_layers=n_layers,
            is_noisy=is_noisy,
            noise_params=noise_params,
        )
        vqc.weights = pnp.array(weights, requires_grad=False)
        vqc.bias = pnp.array(bias, requires_grad=False)
        return vqc


pretrained_model_loader = PretrainedModelLoader()
