"""Model registry schemas."""

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


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
    id: str
    user_id: str
    name: str
    model_type: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelVersionResponse(BaseModel):
    """Specific trained model version record."""
    id: str
    model_id: str
    user_id: str
    version_tag: str
    artifact_id: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
