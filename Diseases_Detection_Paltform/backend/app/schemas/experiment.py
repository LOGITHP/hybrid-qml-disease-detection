from typing_extensions import Annotated
"""Experiment tracking schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BeforeValidator, BaseModel, Field


class ExperimentCreate(BaseModel):
    """Payload to create an experiment tracking container."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ExperimentResponse(BaseModel):
    """Experiment container representation."""
    id: Annotated[str, BeforeValidator(str)]
    user_id: str
    name: str
    description: Optional[str] = None
    tags: List[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
