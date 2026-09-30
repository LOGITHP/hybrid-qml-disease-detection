from typing import Optional, Any, Dict
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class PredictionFeedback(Document):
    prediction_id: str
    model_id: str
    user_id: str
    reviewer_id: Optional[str] = None
    model_version: Optional[str] = None
    is_correct: bool
    verified_label: Optional[int] = None
    original_input: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    status: str = "pending" # pending, used_for_retraining
    used_in_training_run_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "prediction_feedback"
