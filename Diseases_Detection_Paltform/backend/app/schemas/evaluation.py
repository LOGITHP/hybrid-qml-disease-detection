from typing_extensions import Annotated
"""Evaluation metrics and comprehensive multi-model comparison schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BeforeValidator, BaseModel, Field, model_validator


class ConfusionMatrix(BaseModel):
    """Binary classification contingency breakdown."""
    true_positive: int = 0
    true_negative: int = 0
    false_positive: int = 0
    false_negative: int = 0


class EvaluationMetrics(BaseModel):
    """Comprehensive clinical performance metrics."""
    accuracy: float
    sensitivity: float = Field(..., description="Recall: TP / (TP + FN)")
    specificity: float = Field(..., description="TN / (TN + FP)")
    precision: float = Field(..., description="TP / (TP + FP)")
    f1_score: float
    balanced_accuracy: Optional[float] = None
    roc_auc: Optional[float] = None
    confusion_matrix: ConfusionMatrix
    decision_threshold: float = 0.5
    training_duration_sec: Optional[float] = None
    inference_latency_ms: Optional[float] = None


class EvaluationResponse(BaseModel):
    """Stored evaluation run representation."""
    id: Annotated[str, BeforeValidator(str)]
    user_id: str
    model_version_id: str
    dataset_version_id: str
    status: str
    metrics: EvaluationMetrics
    report_artifact_id: Optional[str] = None


class ModelComparisonRequest(BaseModel):
    """Request payload to compare two or more models across all evaluation metrics."""
    model_ids: Optional[List[str]] = Field(None, description="List of model IDs to compare (min 2)")
    model_version_ids: Optional[List[str]] = Field(None, description="List of specific model version IDs to compare (min 2)")
    training_run_ids: Optional[List[str]] = Field(None, description="List of training run IDs to compare (min 2)")

    @model_validator(mode="after")
    def check_min_two_models(self) -> "ModelComparisonRequest":
        count = sum(len(x) for x in [self.model_ids or [], self.model_version_ids or [], self.training_run_ids or []])
        if count < 2:
            raise ValueError("At least 2 models, model versions, or training runs must be selected for comparison.")
        return self


class ModelComparisonEntry(BaseModel):
    """Complete evaluation profile for a single compared model."""
    model_id: str
    model_name: str
    model_type: str  # svm_linear, svm_rbf, vqc
    version_tag: str
    feature_count: int
    selected_features: List[str]
    accuracy: float
    sensitivity: float  # recall
    specificity: float
    precision: float
    f1_score: float
    balanced_accuracy: Optional[float] = None
    roc_auc: Optional[float] = None
    confusion_matrix: ConfusionMatrix
    training_duration_sec: Optional[float] = None
    quantum_details: Optional[Dict[str, Any]] = None


class MetricComparisonRow(BaseModel):
    """A single evaluation metric compared across all selected models."""
    metric_key: str
    display_name: str
    higher_is_better: bool = True
    values: Dict[str, Any]  # model_name -> value
    best_model: str


class ComprehensiveComparisonResponse(BaseModel):
    """Comprehensive comparative evaluation across all metrics for two or more models."""
    models_compared: List[ModelComparisonEntry]
    comparison_matrix: List[MetricComparisonRow]
    category_winners: Dict[str, str]  # e.g., "Highest Accuracy": "Model A"
    cml_vs_qml_insights: Dict[str, Any]
    markdown_table: str
    executive_summary: str
