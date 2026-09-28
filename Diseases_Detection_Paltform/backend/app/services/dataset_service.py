"""Dataset Service."""
import io
import uuid
from typing import Optional
import pandas as pd
from datetime import datetime, timezone
from app.repositories.dataset_repository import DatasetRepository
from app.database.models.dataset import Dataset, DatasetVersion
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.services.artifact_service import artifact_storage, LocalArtifactStorage

class DatasetService:
    def __init__(self, dataset_repo: DatasetRepository = None, storage: Optional[LocalArtifactStorage] = None):
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.storage = storage or artifact_storage
        
    async def list_user_datasets(self, user_id: str):
        return await self.dataset_repo.list_by_user(user_id)
        
    async def create_dataset(self, user_id: str, name: str, description: str = None):
        dataset = Dataset(user_id=user_id, name=name, description=description)
        return await self.dataset_repo.create(dataset)

    async def get_dataset(self, dataset_id: str, user_id: str, is_admin: bool = False):
        dataset = await self.dataset_repo.get_by_id(dataset_id)
        if not dataset:
            raise ResourceNotFoundError("Dataset", dataset_id)
        if dataset.user_id != user_id and not is_admin:
            raise ResourceNotFoundError("Dataset", dataset_id)
        return dataset

    async def delete_dataset(self, dataset_id: str, user_id: str, is_admin: bool = False):
        dataset = await self.get_dataset(dataset_id, user_id, is_admin)
        await self.dataset_repo.delete_versions(dataset_id)
        await self.dataset_repo.delete(dataset)

    async def get_version(self, version_id: str, user_id: str, is_admin: bool = False):
        version = await self.dataset_repo.get_version(version_id)
        if not version:
            raise ResourceNotFoundError("DatasetVersion", version_id)
        return version

    async def upload_version(self, dataset_id: str, user_id: str, file_bytes: bytes, filename: str, version_tag: str, is_admin: bool = False):
        # Validate dataset exists
        dataset = await self.get_dataset(dataset_id, user_id, is_admin)
        
        # Parse CSV
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception:
            raise ValidationError("Invalid CSV file format.")
            
        # Create DB record
        version = DatasetVersion(
            dataset_id=dataset_id,
            user_id=user_id,
            version_tag=version_tag,
            row_count=len(df),
            column_count=len(df.columns),
            status="uploaded"
        )
        created_version = await self.dataset_repo.create_version(version)
        
        # Save artifact
        rel_path = f"datasets/{dataset_id}/versions/{created_version.id}/original.csv"
        self.storage.save(rel_path, file_bytes)
        
        return created_version
        
    async def analyze_version(self, version_id: str, user_id: str, is_admin: bool = False):
        version = await self.get_version(version_id, user_id, is_admin)
        df = self.load_version_dataframe(version.dataset_id, version.id)
        
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        missing = df.isnull().sum().to_dict()
        
        return {
            "dataset_id": version.dataset_id,
            "version_id": version.id,
            "row_count": len(df),
            "column_count": len(df.columns),
            "numerical_columns": num_cols,
            "categorical_columns": cat_cols,
            "missing_value_counts": missing,
        }
        
    def load_version_dataframe(self, dataset_id: str, version_id: str) -> pd.DataFrame:
        rel_path = f"datasets/{dataset_id}/versions/{version_id}/original.csv"
        csv_bytes = self.storage.load(rel_path)
        return pd.read_csv(io.BytesIO(csv_bytes))
