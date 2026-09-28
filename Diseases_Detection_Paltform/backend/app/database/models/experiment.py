"""Experiment ODM."""
from typing import Optional
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class Experiment(Document):
    user_id: str
    name: str
    description: Optional[str] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "experiments"
