"""Artifact metadata and storage response schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    """Artifact metadata representation."""
    id: str
    user_id: str
    name: str
    artifact_type: str
    file_path: str
    file_size_bytes: Optional[int] = None
    mime_type: str
    checksum: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtifactMetadata(BaseModel):
    """File storage registration payload."""
    name: str
    artifact_type: str
    file_size_bytes: int
    mime_type: str
    checksum: str
