"""MongoDB Dataset Repository using Beanie."""
from typing import List, Optional
from beanie.operators import In
from app.database.models.dataset import Dataset, DatasetVersion

class DatasetRepository:
    async def get_by_id(self, dataset_id: str) -> Optional[Dataset]:
        return await Dataset.get(dataset_id)
        
    async def list_by_user(self, user_id: str) -> List[Dataset]:
        return await Dataset.find(Dataset.user_id == user_id).to_list()
        
    async def create(self, dataset: Dataset) -> Dataset:
        return await dataset.insert()
        
    async def get_version(self, version_id: str) -> Optional[DatasetVersion]:
        return await DatasetVersion.get(version_id)
        
    async def create_version(self, version: DatasetVersion) -> DatasetVersion:
        return await version.insert()
        
    async def list_versions(self, dataset_id: str) -> List[DatasetVersion]:
        return await DatasetVersion.find(DatasetVersion.dataset_id == dataset_id).to_list()

    async def delete(self, dataset: Dataset) -> None:
        await dataset.delete()

    async def delete_versions(self, dataset_id: str) -> None:
        await DatasetVersion.find(DatasetVersion.dataset_id == dataset_id).delete()
