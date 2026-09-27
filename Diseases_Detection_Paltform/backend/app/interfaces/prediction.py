"""Inference prediction engine interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import numpy as np


class IPredictionEngine(ABC):
    """Abstract interface for model inference with risk stratification."""

    @abstractmethod
    def predict_with_pipeline(
        self,
        raw_features: List[Dict[str, Any]],
        fitted_pipeline: Any,
        selected_features: List[str],
        trained_model: Any,
        threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Transform raw patient readings with fitted pipeline, filter selected features, and generate predictions."""
        pass
