"""Loader utility for importing existing trained models into the backend application."""

import json
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

    def load_classical_svm(self, model_filename: str) -> Any:
        """Load pre-trained Scikit-Learn SVM (.joblib)."""
        file_path = self.models_dir / model_filename
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
    ) -> VariationalQuantumClassifier:
        """Load pre-trained PennyLane VQC variational weights and bias."""
        w_path = self.models_dir / weights_filename
        b_path = self.models_dir / bias_filename

        if not w_path.exists() or not b_path.exists():
            raise ResourceNotFoundError("VQCWeightsFile", f"{w_path} or {b_path}")

        weights = np.load(w_path)
        bias = np.load(b_path)

        vqc = VariationalQuantumClassifier(
            n_qubits=n_qubits,
            n_layers=n_layers,
            is_noisy=is_noisy,
        )
        vqc.weights = pnp.array(weights, requires_grad=False)
        vqc.bias = pnp.array(bias, requires_grad=False)
        return vqc


pretrained_model_loader = PretrainedModelLoader()
