"""Prediction input and response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class RiskStratification(BaseModel):
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    score: float
    threshold_low_medium: float = 0.35
    threshold_medium_high: float = 0.65
    medical_disclaimer: str = (
        "Model output is a research decision-support signal and is not a medical diagnosis or validated risk estimate."
    )


class PredictionRequest(BaseModel):
    model_id: str
    features: Union[Dict[str, Any], List[Dict[str, Any]]]
    decision_threshold: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)


class SinglePredictionResult(BaseModel):
    predicted_class: int
    predicted_label: str
    probability: Optional[float] = None
    risk_stratification: Optional[RiskStratification] = None
    input_features_used: List[str]
    sample_id: Optional[str] = None


class PredictionResponse(BaseModel):
    model_id: str
    preprocessing_run_id: Optional[str] = None
    feature_selection_run_id: Optional[str] = None
    decision_threshold_applied: float
    results: List[SinglePredictionResult]
    timestamp: datetime
