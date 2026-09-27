"""Authentication and user session schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Payload for creating a new user account."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: Optional[str] = Field(None, max_length=255)


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Bearer token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Payload to refresh an access token."""
    refresh_token: str


class UserProfileResponse(BaseModel):
    """Authenticated user profile representation."""
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
