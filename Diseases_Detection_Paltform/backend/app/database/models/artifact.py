"""Artifact ODM."""
from typing import Optional
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class Artifact(Document):
    user_id: str
    filename: str
    file_path: str
    file_type: str = "csv"
    size_bytes: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "artifacts"
