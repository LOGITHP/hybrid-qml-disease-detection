"""Feature Selection ODM model."""
from typing import Optional, Dict, Any, List
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class FeatureSelectionRun(Document):
    dataset_version_id: str
    user_id: str
    target_column: Optional[str] = None
    status: str = "running"
    ranking_method: str = "mutual_info"
    ranking_data_partition: Optional[str] = None
    ranking_random_state: Optional[int] = None
    feature_count: int
    selected_features: Optional[List[str]] = None
    all_features: Optional[List[str]] = None  # Complete list of available feature columns (excl. target)
    ranking_scores: Optional[Dict[str, float]] = None
    output_dataset_version_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "feature_selection_runs"
