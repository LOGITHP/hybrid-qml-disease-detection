"""Schemas for dataset validation and integrity checking."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ValidationErrorItem(BaseModel):
    """Specific validation error."""
    code: str
    stage: str
    message: str
    recoverable: bool = False
    suggested_fix: Optional[str] = None


class ValidationWarningItem(BaseModel):
    """Specific validation warning."""
    code: str
    stage: str
    message: str


class ValidationResult(BaseModel):
    """Dataset validation summary."""
    status: str = "passed"  # 'passed', 'warning', 'failed'
    passed: bool = True
    errors: List[ValidationErrorItem] = Field(default_factory=list)
    warnings: List[ValidationWarningItem] = Field(default_factory=list)
    checks: Dict[str, bool] = Field(default_factory=dict)
    leakage_detected: bool = False
    train_shape: List[int] = Field(default_factory=list)
    val_shape: List[int] = Field(default_factory=list)
    test_shape: List[int] = Field(default_factory=list)
    feature_count: int = 0
