"""Dataset ODM database model."""
from typing import Optional, Dict, Any
from beanie import Document, Link
from pydantic import Field
from datetime import datetime, timezone
from app.database.models.user import User

class Dataset(Document):
    user_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "datasets"

class DatasetVersion(Document):
    dataset_id: str
    user_id: str
    version_tag: str
    file_artifact_id: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    status: str = "uploaded"
    dataset_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "dataset_versions"
