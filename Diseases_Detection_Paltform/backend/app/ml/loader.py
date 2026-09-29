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

PROJECT_ROOT = _get_project_root()
EXPERIMENT_ROOT = Path(
    os.getenv("EXPERIMENT_ROOT", str(PROJECT_ROOT / "Experimental_ML" / "Lung_Cancer"))
).resolve()


class PretrainedModelLoader:
    """Manages loading of existing pre-trained CML and QML models into backend IModel instances."""

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or PRETRAINED_DIR
        self.metadata_path = self.models_dir / "metadata.json"

    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all pre-trained models with their feature requirements and architectures."""
        experiment_models = self._list_experimental_models()
        if experiment_models:
            return experiment_models
        if not self.metadata_path.exists():
            return []
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("models", [])

    def _list_experimental_models(self) -> List[Dict[str, Any]]:
        """Build the catalog from checkpoints and test metrics in Experimental_ML."""
        if not EXPERIMENT_ROOT.is_dir():
            return []
        consolidated_path = EXPERIMENT_ROOT / "results" / "classical_vs_quantum" / "model_comparison_metrics.json"
        consolidated = {}
        if consolidated_path.exists():
            with open(consolidated_path, "r", encoding="utf-8") as f:
                consolidated = {row.get("Model Name"): row for row in json.load(f) if isinstance(row, dict)}

        model_specs = [
            ("exp-svm-linear-4", "Classical Linear SVM (4 Features)", "svm_linear", 4,
             "CML/4-feature/models/classical_linear_svm_4_feats.joblib", None, None, "Classical Linear SVM (4 Feats)"),
            ("exp-svm-rbf-4", "Classical RBF SVM (4 Features)", "svm_rbf", 4,
             "CML/4-feature/models/classical_rbf_svm_4_feats.joblib", None, None, "Classical RBF SVM (4 Feats)"),
            ("exp-logistic-4", "Logistic Regression (4 Features)", "logistic_regression", 4,
             "CML/4-feature/models/logistic_regression_4_feats.joblib", None, None, "Logistic Regression (4 Feats)"),
            ("exp-svm-linear-6", "Classical Linear SVM (6 Features)", "svm_linear", 6,
             "CML/6-feature/models/classical_linear_svm_6_feats.joblib", None, None, "Classical Linear SVM (6 Feats)"),
            ("exp-svm-rbf-6", "Classical RBF SVM (6 Features)", "svm_rbf", 6,
             "CML/6-feature/models/classical_rbf_svm_6_feats.joblib", None, None, "Classical RBF SVM (6 Feats)"),
            ("exp-svm-linear-8", "Classical Linear SVM (8 Features)", "svm_linear", 8,
             "CML/8-feature/models/classical_linear_svm_8_feats.joblib", None, None, "Classical Linear SVM (8 Feats)"),
            ("exp-svm-rbf-8", "Classical RBF SVM (8 Features)", "svm_rbf", 8,
             "CML/8-feature/models/classical_rbf_svm_8_feats.joblib", None, None, "Classical RBF SVM (8 Feats)"),
            ("exp-vqc-4", "4-Qubit Variational Quantum Classifier (Noiseless)", "vqc", 4,
             None, "HQML/4-feature-VQC/model/vqc_weights.npy", "HQML/4-feature-VQC/model/vqc_bias.npy", "4-Qubit Noiseless VQC"),
            ("exp-vqc-4-noisy", "4-Qubit Variational Quantum Classifier (Noisy NISQ)", "vqc", 4,
             None, "HQML/4-feature-VQC-Noisy/model/vqc_noisy_weights.npy", "HQML/4-feature-VQC-Noisy/model/vqc_noisy_bias.npy", "4-Qubit Noisy VQC"),
            ("exp-vqc-6", "6-Qubit Variational Quantum Classifier", "vqc", 6,
             None, "HQML/6-feature-VQC/model/vqc_6_weights.npy", "HQML/6-feature-VQC/model/vqc_6_bias.npy", "6-Qubit Noiseless VQC"),
            ("exp-vqc-8", "8-Qubit Variational Quantum Classifier", "vqc", 8,
             None, "HQML/8-feature-VQC/model/vqc_8_weights.npy", "HQML/8-feature-VQC/model/vqc_8_bias.npy", "8-Qubit Noiseless VQC"),
        ]
        result = []
        for model_id, name, model_type, feature_count, model_file, weights_file, bias_file, metric_name in model_specs:
            artifact_paths = [path for path in (model_file, weights_file, bias_file) if path]
            if not all((EXPERIMENT_ROOT / path).is_file() for path in artifact_paths):
                continue
            feature_file = "data/processed/selected_features.json" if feature_count == 4 else f"data/processed/selected_features_{feature_count}.json"
            feature_path = EXPERIMENT_ROOT / feature_file
            if not feature_path.is_file():
                continue
            with open(feature_path, "r", encoding="utf-8") as f:
                features = json.load(f)
            metric_row = consolidated.get(metric_name)
            if metric_row is None and model_type in {"svm_linear", "svm_rbf"}:
                metric_path = EXPERIMENT_ROOT / "CML" / f"{feature_count}-feature" / "metrics" / f"metrics_{feature_count}features.json"
                if metric_path.exists():
                    with open(metric_path, "r", encoding="utf-8") as f:
                        metric_row = next((row for row in json.load(f) if row.get("Model Name") == metric_name), None)
            if metric_row is None and model_type == "vqc":
                metrics_paths = {
                    "4-Qubit Noiseless VQC": "HQML/4-feature-VQC/metrics/test_metrics.json",
                    "4-Qubit Noisy VQC": "HQML/4-feature-VQC-Noisy/metrics/noisy_test_metrics.json",
                    "6-Qubit Noiseless VQC": "HQML/6-feature-VQC/metrics/test_metrics_6.json",
                    "8-Qubit Noiseless VQC": "HQML/8-feature-VQC/metrics/test_metrics_8.json",
                }
                metrics_path = EXPERIMENT_ROOT / metrics_paths[metric_name]
                if metrics_path.exists():
                    with open(metrics_path, "r", encoding="utf-8") as f:
                        metric_row = json.load(f)
            metrics = self._normalize_experiment_metrics(metric_row)
            if not metrics:
                continue
            entry = {
                "model_id": model_id,
                "model_name": name,
                "model_type": model_type,
                "feature_count": feature_count,
                "selected_features": features,
                "target_column": "LUNG_CANCER",
                "framework": "PennyLane" if model_type == "vqc" else "scikit-learn",
                "metrics": metrics,
                "source_experiment": str(Path("Experimental_ML") / "Lung_Cancer" / artifact_paths[0]) if model_file else str(Path("Experimental_ML") / "Lung_Cancer" / weights_file),
            }
            if model_file:
                entry["model_file"] = str(Path("Experimental_ML") / "Lung_Cancer" / model_file)
                parameters = metric_row.get("Best Parameters") or metric_row.get("Best Hyperparameters") or {}
                if parameters:
                    entry["hyperparameters"] = parameters
            if weights_file:
                entry["weights_file"] = str(Path("Experimental_ML") / "Lung_Cancer" / weights_file)
                entry["bias_file"] = str(Path("Experimental_ML") / "Lung_Cancer" / bias_file)
                entry.update({"n_qubits": feature_count, "n_layers": 2})
                if "noisy" in model_id:
                    entry["noise_channels"] = {"p_gate": 0.005, "p_cnot": 0.02, "p_meas": 0.015}
            result.append(entry)
        return result

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
