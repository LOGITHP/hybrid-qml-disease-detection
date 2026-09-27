"""Model registry repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.model import Model, ModelConfig, ModelVersion


class ModelRepository:
    """Data access repository for Model archetypes, Configurations, and Versions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, model_id: str, user_id: Optional[str] = None) -> Optional[Model]:
        """Fetch model by UUID."""
        query = select(Model).where(Model.id == model_id)
        if user_id is not None:
            query = query.where(Model.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Model]:
        """List models registered by the user."""
        query = select(Model).where(Model.user_id == user_id).offset(skip).limit(limit)
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
        """Fetch model version by UUID."""
        query = select(ModelVersion).where(ModelVersion.id == version_id)
        if user_id is not None:
            query = query.where(ModelVersion.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
