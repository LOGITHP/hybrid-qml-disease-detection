from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class FeedbackCreate(BaseModel):
    prediction_id: str
    model_id: str
    is_correct: bool
    verified_label: Optional[int] = None
    original_input: Dict[str, Any]
    notes: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: str
    prediction_id: str
    model_id: str
    user_id: str
    is_correct: bool
    verified_label: Optional[int] = None
    original_input: Dict[str, Any]
    notes: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class FeedbackStats(BaseModel):
    total_feedback: int
    correct_predictions: int
    incorrect_predictions: int
    clinician_accuracy: float
    pending_retrain_count: int
