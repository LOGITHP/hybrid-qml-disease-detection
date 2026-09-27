"""Common reusable Pydantic schemas."""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class StandardResponse(BaseModel, Generic[DataT]):
    """Standardized API response wrapper."""
    success: bool = True
    message: str = "Operation completed successfully."
    data: Optional[DataT] = None


class ErrorDetail(BaseModel):
    """Detailed standardized error information."""
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Consistent top-level API error structure."""
    error: ErrorDetail


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated collection response."""
    items: List[DataT]
    pagination: PaginationMeta
