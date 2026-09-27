"""Authentication and user session routes."""

from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_auth_service, get_current_user
from app.database.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
)
from app.schemas.common import StandardResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=StandardResponse[UserProfileResponse], status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account with Argon2id password hashing."""
    user = await auth_service.register(request)
    return StandardResponse(
        message="User account registered successfully.",
        data=UserProfileResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate email and password, returning JWT access and refresh token pair."""
    return await auth_service.login(request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Generate a new access token using a valid refresh token."""
    return await auth_service.refresh_token(request.refresh_token)


@router.post("/logout", response_model=StandardResponse[None])
async def logout(current_user: User = Depends(get_current_user)):
    """Terminate the current authenticated session."""
    return StandardResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Fetch the currently authenticated user's profile and active roles."""
    return UserProfileResponse.model_validate(current_user)
