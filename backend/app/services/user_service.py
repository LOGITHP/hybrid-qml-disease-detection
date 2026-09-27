"""User account management service."""

from typing import List, Optional
from app.core.exceptions import ResourceNotFoundError
from app.database.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    """Service handling user account inquiries and role administration."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_user_by_id(self, user_id: str) -> User:
        """Fetch user by ID or raise 404."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(resource_type="User", resource_id=user_id)
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Admin listing of users."""
        return await self.user_repo.list_all(skip=skip, limit=limit)
