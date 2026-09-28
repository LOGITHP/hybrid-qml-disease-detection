from typing_extensions import Annotated
"""Feature selection and ranking schemas - Single Source of Truth for Models."""

from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BeforeValidator, BaseModel, Field


class FeatureRankingRequest(BaseModel):
    """Request to compute statistical importance scores across dataset features."""
    dataset_version_id: str
    target_column: Optional[str] = None
    method: Literal["mutual_info", "f_classif", "random_forest", "correlation"] = "mutual_info"


class FeatureSelectionRequest(BaseModel):
    """Execute feature selection to produce canonical selected_features."""
    dataset_version_id: str
    preprocessing_run_id: Optional[str] = None
    ranking_method: Literal["mutual_info", "f_classif", "random_forest", "correlation", "manual"] = "mutual_info"
    k_features: Optional[int] = Field(None, ge=1, le=100, description="Number of top features to select")
    selected_features: Optional[List[str]] = Field(None, description="Explicit feature list for manual mode")


class FeatureSelectionResponse(BaseModel):
    """Canonical feature selection record consumed by SVM and VQC models."""
    id: Annotated[str, BeforeValidator(str)]
    dataset_version_id: str
    user_id: str
    preprocessing_run_id: Optional[str] = None
    ranking_method: str
    feature_count: int
    selected_features: List[str]
    ranking_scores: Optional[Dict[str, float]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
