"""Feature Selection ODM model."""
from typing import Optional, Dict, Any, List
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class FeatureSelectionRun(Document):
    dataset_version_id: str
    user_id: str
    status: str = "running"
    method: str = "mutual_information"
    num_features: int
    selected_features: Optional[List[str]] = None
    feature_scores: Optional[Dict[str, float]] = None
    output_dataset_version_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "feature_selection_runs"
