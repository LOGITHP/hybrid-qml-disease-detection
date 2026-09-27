"""Schemas for feature engineering, selection, and dimensionality reduction."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FeatureEngineeringResult(BaseModel):
    """Result of feature engineering operations."""
    status: str = "success"
    applied: bool = False
    transformations: List[Dict[str, Any]] = Field(default_factory=list)
    new_features: List[str] = Field(default_factory=list)
    rationale: str = "No feature engineering applied."


class FeatureScore(BaseModel):
    """Importance score for a feature."""
    feature_name: str
    score: float
    rank: int


class FeatureSelectionResult(BaseModel):
    """Result of feature ranking and selection."""
    status: str = "success"
    method: str
    target_feature_count: Optional[int] = None
    input_feature_count: int
    selected_feature_count: int
    selected_features: List[str] = Field(default_factory=list)
    ranking: List[FeatureScore] = Field(default_factory=list)
    fitted_on: str = "train"


class DimensionalityReductionResult(BaseModel):
    """Result of PCA or other projection methods."""
    status: str = "success"
    applied: bool = False
    method: Optional[str] = None
    n_components: Optional[int] = None
    input_dimensions: int = 0
    output_dimensions: int = 0
    explained_variance_ratio: List[float] = Field(default_factory=list)
    total_explained_variance: float = 0.0
    fitted_on: str = "train"
