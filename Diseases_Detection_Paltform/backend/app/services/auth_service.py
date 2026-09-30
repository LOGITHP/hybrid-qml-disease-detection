"""Auth Service."""
from app.repositories.user_repository import UserRepository
from app.database.models.user import User
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import AuthenticationError, ResourceConflictError

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, request_data) -> User:
        existing = await self.user_repo.get_by_email(request_data.email)
        if existing:
            raise ResourceConflictError("Email already registered.")

        user = User(
            email=request_data.email,
            password_hash=hash_password(request_data.password),
            full_name=request_data.full_name
        )
        return await self.user_repo.create(user)

    async def login(self, request_data):
        user = await self.user_repo.get_by_email(request_data.email)
        if not user or not user.is_active or not verify_password(request_data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")

        return self._token_pair(user)

    async def refresh_token(self, token):
        """Rotate a valid refresh token into a fresh access/refresh pair."""
        claims = decode_token(token, expected_type="refresh")
        user_id = claims.get("sub")
        if not user_id:
            raise AuthenticationError("Refresh token does not identify a user.")
        user = await self.user_repo.get_by_id(str(user_id))
        if not user or not user.is_active:
            raise AuthenticationError("The account associated with this token is unavailable.")
        return self._token_pair(user)

    @staticmethod
    def _token_pair(user: User):
        """Build one response for login and refresh with correctly typed JWTs."""
        from app.core.config import settings

        user_id = str(user.id)
        return {
            "access_token": create_access_token(user_id=user_id, role=user.role),
            "token_type": "bearer",
            "refresh_token": create_refresh_token(user_id=user_id),
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user,
        }
