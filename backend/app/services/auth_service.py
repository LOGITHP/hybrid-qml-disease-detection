"""Authentication and credential validation service."""

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest


class AuthService:
    """Service handling registration, Argon2id verification, and JWT lifecycle."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, request: UserRegisterRequest) -> User:
        """Register a new user account with Argon2id hashed password."""
        email_clean = request.email.lower().strip()
        existing_user = await self.user_repo.get_by_email(email_clean)
        if existing_user:
            raise ResourceConflictError(
                message=f"An account with email '{email_clean}' is already registered."
            )

        if len(request.password) < 8:
            raise ValidationError("Password must be at least 8 characters in length.")

        hashed_pw = hash_password(request.password)
        new_user = User(
            email=email_clean,
            password_hash=hashed_pw,
            full_name=request.full_name,
            role="user",
            is_active=True,
        )
        return await self.user_repo.create(new_user)

    async def login(self, request: UserLoginRequest) -> TokenResponse:
        """Authenticate user credentials and issue JWT access/refresh token pair."""
        email_clean = request.email.lower().strip()
        user = await self.user_repo.get_by_email(email_clean)
        if not user or not verify_password(request.password, user.password_hash):
            raise AuthenticationError("Incorrect email or password.")

        if not user.is_active:
            raise AuthenticationError("This account has been deactivated. Please contact an administrator.")

        access_token = create_access_token(user_id=user.id, role=user.role)
        refresh_token = create_refresh_token(user_id=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        """Validate refresh token and issue a fresh access and refresh token pair."""
        payload = decode_token(refresh_token_str, expected_type="refresh")
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Malformed refresh token.")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User is inactive or no longer exists.")

        new_access_token = create_access_token(user_id=user.id, role=user.role)
        new_refresh_token = create_refresh_token(user_id=user.id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
