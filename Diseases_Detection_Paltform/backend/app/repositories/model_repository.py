"""Model registry repository with support for user-owned and default system models."""

from typing import List, Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.model import Model, ModelConfig, ModelVersion


class ModelRepository:
    """Data access repository for Model archetypes, Configurations, and Versions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, model_id: str, user_id: Optional[str] = None) -> Optional[Model]:
        """Fetch model by UUID, permitting access if owned by user or marked as default for all users."""
        query = select(Model).where(Model.id == model_id)
        if user_id is not None:
            query = query.where(or_(Model.user_id == user_id, Model.is_default.is_(True)))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Model]:
        """Fetch model by unique name."""
        query = select(Model).where(Model.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Model]:
        """List models accessible to the user: their own custom models plus all system-wide default models."""
        query = (
            select(Model)
            .where(or_(Model.user_id == user_id, Model.is_default.is_(True)))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_defaults(self) -> List[Model]:
        """List all system-wide default models available to every user."""
        query = select(Model).where(Model.is_default.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, model: Model) -> Model:
        """Register a new model archetype."""
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def create_version(self, model_version: ModelVersion) -> ModelVersion:
        """Store immutable trained model version."""
        self.session.add(model_version)
        await self.session.flush()
        await self.session.refresh(model_version)
        return model_version

    async def get_version_by_id(self, version_id: str, user_id: Optional[str] = None) -> Optional[ModelVersion]:
        """Fetch model version by UUID, permitting access if owned by user or marked as default."""
        query = select(ModelVersion).where(ModelVersion.id == version_id)
        if user_id is not None:
            query = query.where(or_(ModelVersion.user_id == user_id, ModelVersion.is_default.is_(True)))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
