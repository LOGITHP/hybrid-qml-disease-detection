"""Agent state definitions for LangGraph orchestration matching Section 7."""

from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict

from ..schemas.dataset import DatasetAnalysis
from ..schemas.quality import DataQualityReport
from ..schemas.preprocessing import PreprocessingPlan, TransformationResult
from ..schemas.features import FeatureEngineeringResult, FeatureSelectionResult, DimensionalityReductionResult
from ..schemas.result import DatasetSplitResult, AgentRunResult
from ..schemas.validation import ValidationResult


class PreprocessingState(TypedDict, total=False):
    """Strongly typed serializable LangGraph state for biomedical preprocessing workflow."""
    run_id: str
    dataset_path: str
    dataset_metadata: Dict[str, Any]
    config: Dict[str, Any]

    target_column: Optional[str]
    task_type: Optional[str]

    # Analysis schemas
    dataset_analysis: Optional[DatasetAnalysis]
    quality_report: Optional[DataQualityReport]

    # Plan & Approval
    preprocessing_plan: Optional[PreprocessingPlan]
    approval_status: str  # 'pending', 'approved', 'rejected'
    rejection_reason: Optional[str]

    # Execution tracking
    current_stage: str
    executed_operations: List[TransformationResult]

    # Feature results
    feature_engineering_result: Optional[FeatureEngineeringResult]
    feature_selection_result: Optional[FeatureSelectionResult]
    dimensionality_reduction_result: Optional[DimensionalityReductionResult]

    # Split & Validation
    split_result: Optional[DatasetSplitResult]
    validation_result: Optional[ValidationResult]

    # Recovery
    warnings: List[str]
    errors: List[str]
    retry_count: int
    max_retries: int
    recoverable: bool

    # Final outputs
    output_files: Dict[str, str]
    final_report: Optional[str]
    final_result: Optional[AgentRunResult]
