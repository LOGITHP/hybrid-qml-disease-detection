"""Evaluation metrics and CML vs QML comparison schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConfusionMatrix(BaseModel):
    """Binary classification contingency breakdown."""
    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int


class EvaluationMetrics(BaseModel):
    """Clinical performance metrics."""
    accuracy: float
    sensitivity: float = Field(..., description="Recall: TP / (TP + FN)")
    specificity: float = Field(..., description="TN / (TN + FP)")
    precision: float = Field(..., description="TP / (TP + FP)")
    f1_score: float
    roc_auc: Optional[float] = None
    confusion_matrix: ConfusionMatrix
    decision_threshold: float = 0.5
    training_duration_sec: Optional[float] = None
    inference_latency_ms: Optional[float] = None


class EvaluationResponse(BaseModel):
    """Stored evaluation run representation."""
    id: str
    user_id: str
    model_version_id: str
    dataset_version_id: str
    status: str
    metrics: EvaluationMetrics
    report_artifact_id: Optional[str] = None


class ModelBenchmarkEntry(BaseModel):
    """Comparative row in a CML vs QML benchmark study."""
    model_name: str
    model_type: str  # svm_linear, svm_rbf, vqc
    features_count: int
    metrics: EvaluationMetrics
    quantum_device: Optional[str] = None


class ComparativeEvaluationResponse(BaseModel):
    """Complete comparative study benchmark report (CML vs QML)."""
    dataset_version_id: str
    feature_selection_run_id: str
    selected_features: List[str]
    benchmarks: List[ModelBenchmarkEntry]
    summary_analysis: str
