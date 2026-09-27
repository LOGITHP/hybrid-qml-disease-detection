"""Dataset schemas for metadata, structure, and column profiles."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):
    """Profile of an individual column in the dataset."""
    name: str
    dtype: str
    inferred_type: str  # 'numerical', 'categorical', 'boolean', 'datetime', 'identifier'
    total_count: int
    missing_count: int
    missing_ratio: float
    unique_count: int
    unique_ratio: float
    sample_values: List[Any] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)  # min, max, mean, median, std or mode


class CandidateTarget(BaseModel):
    """Candidate target column identified during schema inspection."""
    column_name: str
    confidence: float
    task_type: str  # 'binary_classification', 'multiclass_classification', 'regression'
    rationale: str
    classes: Optional[List[Any]] = None
    class_counts: Optional[Dict[str, int]] = None


class DatasetAnalysis(BaseModel):
    """Comprehensive dataset analysis output."""
    row_count: int
    column_count: int
    column_names: List[str]
    numerical_features: List[str]
    categorical_features: List[str]
    boolean_features: List[str] = Field(default_factory=list)
    identifier_columns: List[str] = Field(default_factory=list)
    constant_columns: List[str] = Field(default_factory=list)
    near_constant_columns: List[str] = Field(default_factory=list)
    missing_values: Dict[str, int] = Field(default_factory=dict)
    duplicate_rows: int
    columns_profile: Dict[str, ColumnProfile] = Field(default_factory=dict)
    candidate_targets: List[CandidateTarget] = Field(default_factory=list)
    detected_target: Optional[str] = None
    detected_task: Optional[str] = None
