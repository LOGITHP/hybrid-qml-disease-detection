"""User management schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, BeforeValidator
from typing_extensions import Annotated


class UserResponse(BaseModel):
    """User account details."""
    id: Annotated[str, BeforeValidator(str)]
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """User profile update payload."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
