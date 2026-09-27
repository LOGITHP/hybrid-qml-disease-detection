"""Experiment repository for research workflow tracking."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.experiment import Experiment


class ExperimentRepository:
    """Data access repository for Experiment containers."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, experiment_id: str, user_id: Optional[str] = None) -> Optional[Experiment]:
        """Fetch experiment by ID."""
        query = select(Experiment).where(Experiment.id == experiment_id)
        if user_id is not None:
            query = query.where(Experiment.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Experiment]:
        """List experiments created by the user."""
        query = select(Experiment).where(Experiment.user_id == user_id).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, experiment: Experiment) -> Experiment:
        """Create and persist a new experiment container."""
        self.session.add(experiment)
        await self.session.flush()
        await self.session.refresh(experiment)
        return experiment
