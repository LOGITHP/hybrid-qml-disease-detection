"""User repository for database persistence operations."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.user import User


class UserRepository:
    """Data access repository for User entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Fetch user by primary key UUID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        result = await self.session.execute(select(User).where(User.email == email.lower().strip()))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Persist a new user to the database."""
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """Update an existing user."""
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with offset pagination."""
        result = await self.session.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())
