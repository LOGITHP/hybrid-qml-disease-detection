"""Prediction ODM."""
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class Prediction(Document):
    model_id: str
    user_id: str
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    preprocessing_run_id: Optional[str] = None
    feature_selection_run_id: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    prediction_result: float
    probability: Optional[float] = None
    risk_score: Optional[float] = None
    decision_threshold: Optional[float] = 0.5
    explanation_json: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "predictions"
