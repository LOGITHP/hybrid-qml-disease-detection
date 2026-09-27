"""Dataset management and feature selection service enforcing tenant isolation and immutability."""

import io
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import f_classif, mutual_info_classif
from app.core.exceptions import CrossUserAccessError, ResourceNotFoundError, ValidationError
from app.database.models.artifact import Artifact
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.feature_selection import FeatureSelectionRun
from app.repositories.dataset_repository import DatasetRepository
from app.services.artifact_service import LocalArtifactStorage, artifact_storage


class DatasetService:
    """Service handling biomedical dataset ingestion, versioning, statistical profiling, and feature selection."""

    def __init__(self, dataset_repo: DatasetRepository, storage: Optional[LocalArtifactStorage] = None):
        self.dataset_repo = dataset_repo
        self.storage = storage or artifact_storage

    async def create_dataset(self, user_id: str, name: str, description: Optional[str] = None) -> Dataset:
        """Register a new dataset container owned by user_id."""
        dataset = Dataset(user_id=user_id, name=name, description=description)
        return await self.dataset_repo.create_dataset(dataset)

    async def get_dataset(self, dataset_id: str, user_id: str, is_admin: bool = False) -> Dataset:
        """Retrieve dataset ensuring ownership validation."""
        dataset = await self.dataset_repo.get_dataset_by_id(dataset_id)
        if not dataset:
            raise ResourceNotFoundError(resource_type="Dataset", resource_id=dataset_id)
        if not is_admin and dataset.user_id != user_id:
            raise CrossUserAccessError(resource_type="Dataset", resource_id=dataset_id)
        return dataset

    async def list_user_datasets(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Dataset]:
        """List all datasets owned by user."""
        return await self.dataset_repo.list_datasets_by_user(user_id=user_id, skip=skip, limit=limit)

    async def upload_version(
        self,
        dataset_id: str,
        user_id: str,
        file_bytes: bytes,
        filename: str,
        version_tag: str = "v1.0",
        is_admin: bool = False,
    ) -> DatasetVersion:
        """Ingest a CSV dataset version, validate formatting, save immutable original artifact, and record metadata."""
        dataset = await self.get_dataset(dataset_id=dataset_id, user_id=user_id, is_admin=is_admin)

        if not filename.lower().endswith(".csv"):
            raise ValidationError("Only CSV formatted biomedical tabular datasets are currently supported.")

        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValidationError(f"Failed to parse CSV file: {str(e)}")

        row_count, column_count = df.shape
        if row_count < 10:
            raise ValidationError(f"Dataset too small ({row_count} rows). Minimum 10 samples required for screening analysis.")

        version = DatasetVersion(
            dataset_id=dataset.id,
            user_id=user_id,
            version_tag=version_tag,
            row_count=row_count,
            column_count=column_count,
            status="validated",
            dataset_metadata={
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "filename": filename,
            },
        )
        created_version = await self.dataset_repo.create_version(version)

        # Store immutable original dataset in artifact storage
        storage_rel_path = f"datasets/{dataset.id}/versions/{created_version.id}/original.csv"
        self.storage.save(storage_rel_path, file_bytes)

        return created_version

    async def get_version(self, version_id: str, user_id: str, is_admin: bool = False) -> DatasetVersion:
        """Fetch dataset version with authorization check."""
        version = await self.dataset_repo.get_version_by_id(version_id)
        if not version:
            raise ResourceNotFoundError(resource_type="DatasetVersion", resource_id=version_id)
        if not is_admin and version.user_id != user_id:
            raise CrossUserAccessError(resource_type="DatasetVersion", resource_id=version_id)
        return version

    def load_version_dataframe(self, dataset_id: str, version_id: str) -> pd.DataFrame:
        """Load stored dataset version into a pandas DataFrame."""
        storage_rel_path = f"datasets/{dataset_id}/versions/{version_id}/original.csv"
        data_bytes = self.storage.load(storage_rel_path)
        return pd.read_csv(io.BytesIO(data_bytes))

    async def analyze_version(self, version_id: str, user_id: str, is_admin: bool = False) -> Dict[str, Any]:
        """Compute statistical summary for LLM reasoning without sending raw patient records."""
        version = await self.get_version(version_id=version_id, user_id=user_id, is_admin=is_admin)
        df = self.load_version_dataframe(dataset_id=version.dataset_id, version_id=version.id)

        numerical_cols = list(df.select_dtypes(include=[np.number]).columns)
        categorical_cols = list(df.select_dtypes(exclude=[np.number]).columns)
        missing_counts = {col: int(df[col].isna().sum()) for col in df.columns}

        return {
            "dataset_id": version.dataset_id,
            "version_id": version.id,
            "row_count": len(df),
            "column_count": len(df.columns),
            "numerical_columns": numerical_cols,
            "categorical_columns": categorical_cols,
            "missing_value_counts": missing_counts,
        }

    async def execute_feature_selection(
        self,
        dataset_version_id: str,
        user_id: str,
        target_column: str,
        ranking_method: str = "mutual_info",
        k_features: int = 4,
        is_admin: bool = False,
    ) -> FeatureSelectionRun:
        """Perform feature ranking and selection.
        
        CRITICAL ARCHITECTURAL PRINCIPLE:
        This is the SINGLE SOURCE OF TRUTH for selected features consumed by both CML and QML models.
        """
        version = await self.get_version(version_id=dataset_version_id, user_id=user_id, is_admin=is_admin)
        df = self.load_version_dataframe(dataset_id=version.dataset_id, version_id=version.id)

        if target_column not in df.columns:
            raise ValidationError(f"Target column '{target_column}' does not exist in dataset.")

        # Separate features and target
        X_df = df.drop(columns=[target_column]).select_dtypes(include=[np.number]).fillna(0)
        y = df[target_column].values

        feature_names = list(X_df.columns)
        if len(feature_names) < k_features:
            k_features = len(feature_names)

        ranking_scores: Dict[str, float] = {}
        if ranking_method == "mutual_info":
            scores = mutual_info_classif(X_df.values, y, random_state=42)
            ranking_scores = {feature_names[i]: float(scores[i]) for i in range(len(feature_names))}
        elif ranking_method == "f_classif":
            f_vals, _ = f_classif(X_df.values, y)
            f_vals = np.nan_to_num(f_vals, nan=0.0)
            ranking_scores = {feature_names[i]: float(f_vals[i]) for i in range(len(feature_names))}
        elif ranking_method == "random_forest":
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X_df.values, y)
            ranking_scores = {feature_names[i]: float(rf.feature_importances_[i]) for i in range(len(feature_names))}
        else:
            # Fallback correlation
            corrs = [abs(np.corrcoef(X_df.iloc[:, i], y)[0, 1]) for i in range(len(feature_names))]
            ranking_scores = {feature_names[i]: float(np.nan_to_num(corrs[i])) for i in range(len(feature_names))}

        # Rank features descending by score
        sorted_features = sorted(ranking_scores.items(), key=lambda item: item[1], reverse=True)
        selected = [item[0] for item in sorted_features[:k_features]]

        fs_run = FeatureSelectionRun(
            dataset_version_id=version.id,
            user_id=user_id,
            ranking_method=ranking_method,
            feature_count=len(selected),
            selected_features=selected,
            ranking_scores=ranking_scores,
        )
        return await self.dataset_repo.create_feature_selection_run(fs_run)
