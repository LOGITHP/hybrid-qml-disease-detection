"""Inference prediction and disease risk stratification schemas."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class RiskStratification(BaseModel):
    """Categorical risk assessment with clinical decision support disclaimer."""
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    score: float
    threshold_low_medium: float = 0.35
    threshold_medium_high: float = 0.65
    medical_disclaimer: str = (
        "Application risk categories reflect statistical model predictions and are strictly intended "
        "for investigative research and decision support. They do NOT constitute a definitive medical diagnosis."
    )


class PredictionRequest(BaseModel):
    """Payload for real-time model inference."""
    model_version_id: str
    features: Union[Dict[str, float], List[Dict[str, float]]] = Field(
        ...,
        description="Patient biomarker readings mapped by feature name, or list of patients."
    )
    decision_threshold: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)


class SinglePredictionResult(BaseModel):
    """Single sample prediction output."""
    predicted_class: int
    predicted_label: str
    probability: Optional[float] = None
    risk_stratification: Optional[RiskStratification] = None
    input_features_used: List[str]
    sample_id: Optional[str] = None


class PredictionResponse(BaseModel):
    """Complete prediction inference response."""
    model_version_id: str
    preprocessing_run_id: Optional[str] = None
    feature_selection_run_id: Optional[str] = None
    decision_threshold_applied: float
    results: List[SinglePredictionResult]
    timestamp: datetime
