"""Experiment ODM."""
from typing import List, Optional
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class Experiment(Document):
    user_id: str
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    dataset_name: Optional[str] = None
    preprocessing_run_id: Optional[str] = None
    feature_selection_run_id: Optional[str] = None
    target_column: Optional[str] = None
    selected_features: List[str] = Field(default_factory=list)
    training_run_ids: List[str] = Field(default_factory=list)
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "experiments"
