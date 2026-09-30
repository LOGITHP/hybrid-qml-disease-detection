from typing import Optional, Dict, Any
from typing_extensions import Annotated
from pydantic import BeforeValidator, BaseModel
from datetime import datetime

class FeedbackCreate(BaseModel):
    prediction_id: str
    model_id: str
    is_correct: bool
    verified_label: Optional[int] = None
    original_input: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)]
    prediction_id: str
    model_id: str
    user_id: str
    reviewer_id: Optional[str] = None
    model_version: Optional[str] = None
    is_correct: bool
    verified_label: Optional[int] = None
    original_input: Dict[str, Any]
    notes: Optional[str] = None
    status: str
    used_in_training_run_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FeedbackStats(BaseModel):
    total_feedback: int
    correct_predictions: int
    incorrect_predictions: int
    clinician_accuracy: float
    pending_retrain_count: int
