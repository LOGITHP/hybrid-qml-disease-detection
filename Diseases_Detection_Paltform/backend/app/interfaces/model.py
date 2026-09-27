"""Model architecture interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import numpy as np


class IModel(ABC):
    """Abstract interface for all Classical and Quantum classification models."""

    @property
    @abstractmethod
    def model_type(self) -> str:
        """Returns model identifier: svm_linear, svm_rbf, or vqc."""
        pass

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs: Any) -> "IModel":
        """Train model parameters on input features and labels."""
        pass

    @abstractmethod
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Generate binary class predictions."""
        pass

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Generate class probability estimates."""
        pass

    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """Return model hyperparameters."""
        pass
