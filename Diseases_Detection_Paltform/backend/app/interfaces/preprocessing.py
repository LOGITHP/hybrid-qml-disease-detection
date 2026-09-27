"""Preprocessing engine interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict
import pandas as pd
from app.schemas.preprocessing import PreprocessingPlan


class IPreprocessingEngine(ABC):
    """Abstract interface for dataset preprocessing and cleaning."""

    @abstractmethod
    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute statistical summary, class imbalance, and data quality metrics."""
        pass

    @abstractmethod
    def generate_plan(self, df: pd.DataFrame, target_column: str) -> PreprocessingPlan:
        """Formulate a structured transformation plan preventing data leakage."""
        pass

    @abstractmethod
    def execute_plan(
        self,
        df: pd.DataFrame,
        plan: PreprocessingPlan,
        target_column: str,
    ) -> Dict[str, Any]:
        """Execute plan deterministically and return train/val/test splits and fitted pipeline."""
        pass
