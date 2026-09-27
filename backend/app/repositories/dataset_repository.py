"""Dataset repository enforcing strict multi-user isolation."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.preprocessing import PreprocessingRun, PreprocessingConfig
from app.database.models.feature_selection import FeatureSelectionRun


class DatasetRepository:
    """Data access repository for Datasets, Versions, PreprocessingRuns, and FeatureSelectionRuns."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dataset_by_id(self, dataset_id: str, user_id: Optional[str] = None) -> Optional[Dataset]:
        """Fetch dataset with optional user ownership check."""
        query = select(Dataset).where(Dataset.id == dataset_id)
        if user_id is not None:
            query = query.where(Dataset.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_datasets_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Dataset]:
        """List datasets owned by the specified user."""
        query = select(Dataset).where(Dataset.user_id == user_id).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_dataset(self, dataset: Dataset) -> Dataset:
        """Create and persist a new dataset entity."""
        self.session.add(dataset)
        await self.session.flush()
        await self.session.refresh(dataset)
        return dataset

    async def get_version_by_id(self, version_id: str, user_id: Optional[str] = None) -> Optional[DatasetVersion]:
        """Fetch dataset version by UUID."""
        query = select(DatasetVersion).where(DatasetVersion.id == version_id)
        if user_id is not None:
            query = query.where(DatasetVersion.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_versions_by_dataset(self, dataset_id: str, user_id: Optional[str] = None) -> List[DatasetVersion]:
        """List all versions associated with a dataset."""
        query = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id)
        if user_id is not None:
            query = query.where(DatasetVersion.user_id == user_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_version(self, version: DatasetVersion) -> DatasetVersion:
        """Create and persist a dataset version."""
        self.session.add(version)
        await self.session.flush()
        await self.session.refresh(version)
        return version

    async def create_preprocessing_run(self, run: PreprocessingRun) -> PreprocessingRun:
        """Persist a preprocessing execution run."""
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)
        return run

    async def get_preprocessing_run(self, run_id: str, user_id: Optional[str] = None) -> Optional[PreprocessingRun]:
        """Fetch preprocessing run with user authorization check."""
        query = select(PreprocessingRun).where(PreprocessingRun.id == run_id)
        if user_id is not None:
            query = query.where(PreprocessingRun.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_feature_selection_run(self, run: FeatureSelectionRun) -> FeatureSelectionRun:
        """Persist canonical feature selection run (Single Source of Truth)."""
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)
        return run

    async def get_feature_selection_run(self, run_id: str, user_id: Optional[str] = None) -> Optional[FeatureSelectionRun]:
        """Fetch feature selection run with user authorization check."""
        query = select(FeatureSelectionRun).where(FeatureSelectionRun.id == run_id)
        if user_id is not None:
            query = query.where(FeatureSelectionRun.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
