"""Dataset Service."""
import io
import uuid
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from app.repositories.dataset_repository import DatasetRepository
from app.database.models.dataset import Dataset, DatasetVersion
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.services.artifact_service import artifact_storage, LocalArtifactStorage
from app.agents.preprocessing_agent.tools.dataset_analysis import rank_target_candidates

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
        if version.user_id != user_id and not is_admin:
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

        if df.empty or len(df.columns) == 0:
            raise ValidationError("The uploaded CSV must contain at least one row and one column.")
            
        # Create DB record
        version = DatasetVersion(
            dataset_id=dataset_id,
            user_id=user_id,
            version_tag=version_tag,
            row_count=len(df),
            column_count=len(df.columns),
            status="uploaded",
            dataset_metadata={
                "filename": filename,
                "format": "csv",
                "file_size_bytes": len(file_bytes),
                "columns": [str(column) for column in df.columns],
                "dtypes": {str(column): str(dtype) for column, dtype in df.dtypes.items()},
            },
        )
        created_version = await self.dataset_repo.create_version(version)
        
        # Save artifact
        rel_path = f"datasets/{dataset_id}/versions/{created_version.id}/original.csv"
        self.storage.save(rel_path, file_bytes)
        
        return created_version
        
    async def analyze_version(
        self,
        version_id: str,
        user_id: str,
        is_admin: bool = False,
        target_column: Optional[str] = None,
    ):
        version = await self.get_version(version_id, user_id, is_admin)
        df = self.load_version_dataframe(version.dataset_id, version.id)

        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
        missing = {str(column): int(count) for column, count in df.isna().sum().items()}

        target_candidates = rank_target_candidates(df, target_hint=target_column)
        target_guess = target_column or (target_candidates[0].column_name if target_candidates else None)
        if target_guess is not None and target_guess not in df.columns:
            raise ValidationError(f"Target column '{target_guess}' not found in dataset.")

        class_distribution: Dict[str, int] = {}
        if target_guess:
            class_distribution = {
                str(label): int(count)
                for label, count in df[target_guess].value_counts(dropna=True).items()
            }

        column_profiles: Dict[str, Dict[str, Any]] = {}
        for column in df.columns:
            series = df[column]
            profile: Dict[str, Any] = {
                "dtype": str(series.dtype),
                "missing_count": int(series.isna().sum()),
                "missing_percent": round(float(series.isna().mean() * 100), 2) if len(series) else 0.0,
                "unique_count": int(series.nunique(dropna=True)),
                "sample_values": [self._json_scalar(value) for value in series.dropna().unique()[:5]],
            }
            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                numeric = pd.to_numeric(series, errors="coerce").dropna()
                numeric = numeric[np.isfinite(numeric.to_numpy(dtype=float))]
                if not numeric.empty:
                    profile["statistics"] = {
                        "count": int(numeric.count()),
                        "mean": self._json_scalar(numeric.mean()),
                        "std": self._json_scalar(numeric.std()),
                        "min": self._json_scalar(numeric.min()),
                        "25%": self._json_scalar(numeric.quantile(0.25)),
                        "median": self._json_scalar(numeric.median()),
                        "75%": self._json_scalar(numeric.quantile(0.75)),
                        "max": self._json_scalar(numeric.max()),
                    }
                    if numeric.nunique() <= 12:
                        profile["distribution"] = [
                            {"value": self._json_scalar(value), "count": int(count)}
                            for value, count in numeric.value_counts().sort_index().items()
                        ]
                    else:
                        counts, edges = np.histogram(numeric.to_numpy(dtype=float), bins=min(10, max(2, int(np.sqrt(len(numeric))))))
                        profile["distribution"] = [
                            {"lower": self._json_scalar(edges[index]), "upper": self._json_scalar(edges[index + 1]), "count": int(count)}
                            for index, count in enumerate(counts)
                        ]
            else:
                frequencies = series.value_counts(dropna=False).head(10)
                profile["distribution"] = [
                    {"value": self._json_scalar(value), "count": int(count)}
                    for value, count in frequencies.items()
                ]
                profile["statistics"] = {
                    "mode": self._json_scalar(series.mode(dropna=True).iloc[0]) if not series.mode(dropna=True).empty else None,
                }
            column_profiles[str(column)] = profile

        metadata = version.dataset_metadata or {}

        return {
            "dataset_id": str(version.dataset_id),
            "version_id": str(version.id),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": [str(column) for column in df.columns],
            "dtypes": {str(column): str(dtype) for column, dtype in df.dtypes.items()},
            "numerical_columns": [str(column) for column in num_cols],
            "categorical_columns": [str(column) for column in cat_cols],
            "missing_value_counts": missing,
            "column_profiles": column_profiles,
            "duplicate_row_count": int(df.duplicated().sum()),
            "file_metadata": {
                "filename": metadata.get("filename", "uploaded.csv"),
                "format": metadata.get("format", "csv"),
                "file_size_bytes": metadata.get("file_size_bytes"),
                "version_tag": version.version_tag,
                "created_at": version.created_at.isoformat(),
            },
            "target_column": target_guess,
            "target_candidates": [
                {
                    "column_name": candidate.column_name,
                    "confidence": candidate.confidence,
                    "task_type": candidate.task_type,
                    "rationale": candidate.rationale,
                    "class_counts": candidate.class_counts,
                }
                for candidate in target_candidates
            ],
            "class_distribution": class_distribution,
        }

    @staticmethod
    def _json_scalar(value: Any):
        """Convert pandas/numpy scalar values into JSON-safe native values."""
        if pd.isna(value):
            return None
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, (int, float, str, bool)) or value is None:
            if isinstance(value, float) and not np.isfinite(value):
                return None
            return value
        return str(value)
        
    def load_version_dataframe(self, dataset_id: str, version_id: str) -> pd.DataFrame:
        rel_path = f"datasets/{dataset_id}/versions/{version_id}/original.csv"
        csv_bytes = self.storage.load(rel_path)
        return pd.read_csv(io.BytesIO(csv_bytes))

    async def execute_feature_selection(
        self,
        dataset_version_id: str,
        user_id: str,
        target_column: str,
        ranking_method: str,
        k_features: int,
        is_admin: bool = False,
        selected_features: Optional[List[str]] = None,
    ):
        version = await self.get_version(dataset_version_id, user_id, is_admin)
        df = self.load_version_dataframe(version.dataset_id, version.id)

        if target_column not in df.columns:
            raise ValidationError(f"Target column '{target_column}' not found in dataset.")

        feature_columns = [str(col) for col in df.columns if col != target_column]
        if not feature_columns:
            raise ValidationError("The dataset has no feature columns after selecting the target.")
        y = df[target_column]
        class_count = int(y.nunique(dropna=True))
        if y.isna().any() or class_count < 2:
            raise ValidationError("The target must have at least two classes and no missing values before feature ranking.")
        if class_count > max(20, int(len(df) * 0.5)):
            raise ValidationError("The selected target looks continuous or high-cardinality; choose a classification target column.")

        ranking_scores: Dict[str, float] = {}
        if ranking_method == "manual":
            requested = list(dict.fromkeys(selected_features or []))
            if not requested:
                raise ValidationError("Choose at least one feature for manual selection.")
            invalid = [column for column in requested if column not in feature_columns]
            if invalid:
                raise ValidationError(f"Selected feature columns are not available: {', '.join(invalid)}.")
            chosen_features = requested
        else:
            numeric_columns = [
                column for column in feature_columns
                if pd.api.types.is_numeric_dtype(df[column]) and not pd.api.types.is_bool_dtype(df[column])
            ]
            categorical_columns = [column for column in feature_columns if column not in numeric_columns]
            transformers = []
            if numeric_columns:
                from sklearn.impute import SimpleImputer
                transformers.append(("numeric", SimpleImputer(strategy="median", keep_empty_features=True), numeric_columns))
            if categorical_columns:
                from sklearn.impute import SimpleImputer
                from sklearn.pipeline import Pipeline
                from sklearn.preprocessing import OneHotEncoder
                transformers.append(("categorical", Pipeline([
                    ("imputer", SimpleImputer(strategy="constant", fill_value="__missing__")),
                    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                ]), categorical_columns))
            from sklearn.compose import ColumnTransformer
            transformer = ColumnTransformer(transformers, verbose_feature_names_out=True)
            feature_frame = df[feature_columns].replace([np.inf, -np.inf], np.nan)
            for column in categorical_columns:
                feature_frame[column] = feature_frame[column].apply(
                    lambda value: np.nan if pd.isna(value) else str(value)
                )
            matrix = np.asarray(transformer.fit_transform(feature_frame), dtype=float)
            if not np.isfinite(matrix).all():
                raise ValidationError("Feature preprocessing produced non-finite values. Check columns with only missing or infinite data.")
            encoded_names = [str(name) for name in transformer.get_feature_names_out()]
            source_columns: List[str] = []
            for encoded_name in encoded_names:
                if encoded_name.startswith("numeric__"):
                    source_columns.append(encoded_name[len("numeric__"):])
                else:
                    matches = [column for column in categorical_columns if encoded_name.startswith(f"categorical__{column}_")]
                    if not matches:
                        raise ValidationError(f"Unable to map encoded feature '{encoded_name}' to its source column.")
                    source_columns.append(max(matches, key=len))

            from sklearn.preprocessing import LabelEncoder
            encoded_target = LabelEncoder().fit_transform(y.astype(str))
            if ranking_method == "mutual_info":
                from sklearn.feature_selection import mutual_info_classif
                discrete_mask = np.asarray([name.startswith("categorical__") for name in encoded_names], dtype=bool)
                scores = mutual_info_classif(matrix, encoded_target, discrete_features=discrete_mask, random_state=42)
            elif ranking_method == "f_classif":
                from sklearn.feature_selection import f_classif
                scores, _ = f_classif(matrix, encoded_target)
            elif ranking_method == "random_forest":
                from sklearn.ensemble import RandomForestClassifier
                estimator = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
                estimator.fit(matrix, encoded_target)
                scores = estimator.feature_importances_
            elif ranking_method == "lasso":
                from sklearn.linear_model import LogisticRegression
                from sklearn.preprocessing import StandardScaler
                estimator = LogisticRegression(
                    penalty="l1", solver="liblinear", C=1.0, max_iter=2000,
                    class_weight="balanced", random_state=42,
                )
                estimator.fit(StandardScaler().fit_transform(matrix), encoded_target)
                scores = np.mean(np.abs(estimator.coef_), axis=0)
            elif ranking_method == "correlation":
                scores = np.asarray([
                    abs(float(np.corrcoef(matrix[:, index], encoded_target)[0, 1]))
                    if np.std(matrix[:, index]) > 0 else 0.0
                    for index in range(matrix.shape[1])
                ])
            else:
                raise ValidationError(f"Unsupported feature-ranking method '{ranking_method}'.")

            grouped_scores: Dict[str, List[float]] = {column: [] for column in feature_columns}
            for source, score in zip(source_columns, scores):
                if np.isfinite(score):
                    grouped_scores[source].append(float(score))
            ranking_scores = {
                column: float(sum(values)) if values else 0.0
                for column, values in grouped_scores.items()
            }
            sorted_features = sorted(ranking_scores.items(), key=lambda item: (-item[1], item[0]))
            limit = min(max(int(k_features), 1), len(sorted_features))
            chosen_features = [feature for feature, _ in sorted_features[:limit]]

        from app.database.models.feature_selection import FeatureSelectionRun
        fs_run = FeatureSelectionRun(
            dataset_version_id=dataset_version_id,
            user_id=user_id,
            target_column=target_column,
            ranking_method=ranking_method,
            feature_count=len(chosen_features),
            selected_features=chosen_features,
            ranking_scores=ranking_scores,
            status="completed"
        )
        await fs_run.insert()
        return fs_run
