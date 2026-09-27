"""Data quality schemas for anomaly detection, duplicates, and leakage checks."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class QualityFinding(BaseModel):
    """Specific quality issue or observation detected."""
    severity: str  # 'info', 'warning', 'critical'
    category: str  # 'missing_values', 'duplicates', 'outliers', 'leakage', 'imbalance', etc.
    affected_columns: List[str] = Field(default_factory=list)
    description: str
    recommended_action: str


class DataQualityReport(BaseModel):
    """Aggregate data quality assessment."""
    status: str = "success"
    missing_value_summary: Dict[str, Any] = Field(default_factory=dict)
    duplicate_summary: Dict[str, Any] = Field(default_factory=dict)
    invalid_value_summary: Dict[str, Any] = Field(default_factory=dict)
    inconsistent_categories_summary: Dict[str, Any] = Field(default_factory=dict)
    outlier_summary: Dict[str, Any] = Field(default_factory=dict)
    constant_feature_summary: Dict[str, Any] = Field(default_factory=dict)
    high_correlation_pairs: List[Dict[str, Any]] = Field(default_factory=list)
    class_imbalance_summary: Dict[str, Any] = Field(default_factory=dict)
    target_leakage_risk: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[QualityFinding] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
