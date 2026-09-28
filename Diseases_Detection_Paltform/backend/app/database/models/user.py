"""User ODM database model."""
from typing import Optional
from beanie import Document
from pydantic import EmailStr, Field
from datetime import datetime, timezone

class User(Document):
    email: EmailStr
    password_hash: str
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "users"
        indexes = ["email"]
