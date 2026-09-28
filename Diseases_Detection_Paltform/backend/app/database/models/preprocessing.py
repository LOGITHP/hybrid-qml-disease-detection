"""Preprocessing ODM model."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class PreprocessingRun(Document):
    dataset_version_id: str
    user_id: str
    status: str = "running"
    config_params: Dict[str, Any] = Field(default_factory=dict)
    imputation_strategy: Optional[str] = None
    scaling_strategy: Optional[str] = None
    encoding_strategy: Optional[str] = None
    output_dataset_version_id: Optional[str] = None
    scaler_artifact_id: Optional[str] = None
    imputer_artifact_id: Optional[str] = None
    encoder_artifact_id: Optional[str] = None
    ai_recommendation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "preprocessing_runs"
