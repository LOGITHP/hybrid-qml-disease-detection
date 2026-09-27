"""Model training engine interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict
import numpy as np
from app.interfaces.model import IModel


class ITrainingEngine(ABC):
    """Abstract interface for training orchestration across Classical and Quantum ML models."""

    @abstractmethod
    def train(
        self,
        model: IModel,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        training_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute model training loop and evaluate on validation split. Returns trained model and metrics."""
        pass
