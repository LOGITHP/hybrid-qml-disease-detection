"""Schemas for final structured agent execution results and reports."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .dataset import DatasetAnalysis
from .quality import DataQualityReport
from .preprocessing import PreprocessingPlan, TransformationResult
from .features import FeatureEngineeringResult, FeatureSelectionResult, DimensionalityReductionResult
from .validation import ValidationResult


class DatasetSplitResult(BaseModel):
    """Result of train/validation/test splitting."""
    status: str = "success"
    random_state: int
    train_ratio: float
    val_ratio: float
    test_ratio: float
    train_samples: int
    val_samples: int
    test_samples: int
    target_column: str
    stratified: bool
    train_class_distribution: Dict[str, int] = Field(default_factory=dict)
    val_class_distribution: Dict[str, int] = Field(default_factory=dict)
    test_class_distribution: Dict[str, int] = Field(default_factory=dict)


class AgentRunResult(BaseModel):
    """Comprehensive structured outcome of an agent run."""
    run_id: str
    status: str  # 'success', 'warning', 'error', 'waiting_for_approval'
    dataset_path: str
    target_column: Optional[str] = None
    task_type: Optional[str] = None
    dataset_analysis: Optional[DatasetAnalysis] = None
    quality_report: Optional[DataQualityReport] = None
    preprocessing_plan: Optional[PreprocessingPlan] = None
    executed_operations: List[TransformationResult] = Field(default_factory=list)
    feature_engineering: Optional[FeatureEngineeringResult] = None
    feature_selection: Optional[FeatureSelectionResult] = None
    dimensionality_reduction: Optional[DimensionalityReductionResult] = None
    split_result: Optional[DatasetSplitResult] = None
    validation: Optional[ValidationResult] = None
    output_files: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
