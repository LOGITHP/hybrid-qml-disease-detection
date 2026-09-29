from typing_extensions import Annotated
"""Model registry schemas."""

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BeforeValidator, BaseModel, Field


class ModelCreate(BaseModel):
    """Register a new model archetype in registry."""
    name: str = Field(..., max_length=255)
    model_type: Literal["svm_linear", "svm_rbf", "vqc"]
    description: Optional[str] = None


class ModelConfigCreate(BaseModel):
    """Define architectural and hyperparameter configuration for a model."""
    name: str
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    """Model registry entry representation."""
    id: Annotated[str, BeforeValidator(str)]
    user_id: Optional[str] = None
    name: str
    model_type: str
    description: Optional[str] = None
    is_default: bool = False
    status: str = "created"
    configuration: Dict[str, Any] = Field(default_factory=dict)
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    preprocessing_run_id: Optional[str] = None
    feature_selection_run_id: Optional[str] = None
    selected_features_snapshot: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelVersionResponse(BaseModel):
    """Specific trained model version record."""
    id: Annotated[str, BeforeValidator(str)]
    model_id: str
    user_id: Optional[str] = None
    version_tag: str
    artifact_id: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    status: str
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
