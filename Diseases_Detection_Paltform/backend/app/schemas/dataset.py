"""Dataset and dataset version schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    """Payload to register a new dataset record."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    """Dataset metadata representation."""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetVersionResponse(BaseModel):
    """Dataset version record."""
    id: str
    dataset_id: str
    user_id: str
    version_tag: str
    file_artifact_id: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    status: str
    dataset_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetAnalysisSummary(BaseModel):
    """Structured statistical summary computed from an uploaded dataset without raw records."""
    dataset_id: str
    version_id: str
    row_count: int
    column_count: int
    numerical_columns: List[str]
    categorical_columns: List[str]
    missing_value_counts: Dict[str, int]
    target_distribution: Optional[Dict[str, int]] = None
    class_imbalance_ratio: Optional[float] = None
