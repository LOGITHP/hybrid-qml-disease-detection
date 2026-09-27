"""Training configuration and execution run schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TrainingConfigCreate(BaseModel):
    """Training hyperparameter definition."""
    name: str
    epochs: Optional[int] = Field(None, ge=1, le=1000)
    batch_size: Optional[int] = Field(None, ge=1, le=4096)
    learning_rate: Optional[float] = Field(None, gt=0.0, le=1.0)
    optimizer: Optional[str] = "Adam"
    random_seed: int = 42
    early_stopping: bool = True
    extra_config: Dict[str, Any] = Field(default_factory=dict)


class TrainingRunCreate(BaseModel):
    """Initiate a model training run."""
    model_id: str
    dataset_version_id: str
    feature_selection_run_id: str
    preprocessing_run_id: Optional[str] = None
    training_config_id: Optional[str] = None
    experiment_id: Optional[str] = None


class TrainingRunResponse(BaseModel):
    """Training run state and performance summary."""
    id: str
    user_id: str
    model_id: str
    model_version_id: Optional[str] = None
    dataset_version_id: str
    preprocessing_run_id: Optional[str] = None
    feature_selection_run_id: str
    status: str
    metrics: Optional[Dict[str, Any]] = None
    artifact_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
