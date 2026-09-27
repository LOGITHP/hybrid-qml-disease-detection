"""End-to-end serializable preprocessing pipeline for reproducible inference."""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import joblib
import pandas as pd

from ..tools.cleaning import MissingValueImputer
from ..tools.encoding import CategoricalEncoder, TargetLabelEncoder
from ..tools.scaling import NumericalScaler
from ..tools.outliers import OutlierHandler
from ..tools.feature_selection import FeatureSelector
from ..tools.dimensionality_reduction import DimensionalityReducer


class PreprocessingPipeline:
    """Serializable container bundling all fitted transformers for production inference."""

    def __init__(
        self,
        imputer: Optional[MissingValueImputer] = None,
        outlier_handler: Optional[OutlierHandler] = None,
        categorical_encoder: Optional[CategoricalEncoder] = None,
        target_encoder: Optional[TargetLabelEncoder] = None,
        scaler: Optional[NumericalScaler] = None,
        feature_selector: Optional[FeatureSelector] = None,
        dimensionality_reducer: Optional[DimensionalityReducer] = None,
        selected_features: Optional[List[str]] = None,
        target_column: Optional[str] = None
    ):
        self.imputer = imputer
        self.outlier_handler = outlier_handler
        self.categorical_encoder = categorical_encoder
        self.target_encoder = target_encoder
        self.scaler = scaler
        self.feature_selector = feature_selector
        self.dimensionality_reducer = dimensionality_reducer
        self.selected_features = selected_features or []
        self.target_column = target_column

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforms unseen inference records through the exact fitted pipeline."""
        df_out = df.copy()

        # Drop target if present during feature transformation
        if self.target_column and self.target_column in df_out.columns:
            df_out = df_out.drop(columns=[self.target_column])

        # Step 1: Missing value imputation
        if self.imputer:
            df_out = self.imputer.transform(df_out)

        # Step 2: Outlier clipping
        if self.outlier_handler:
            df_out = self.outlier_handler.transform(df_out)

        # Step 3: Categorical encoding
        if self.categorical_encoder:
            df_out = self.categorical_encoder.transform(df_out)

        # Step 4: Numerical scaling
        if self.scaler:
            df_out = self.scaler.transform(df_out)

        # Step 5: Feature selection
        if self.feature_selector:
            df_out = self.feature_selector.transform(df_out)

        # Step 6: Dimensionality reduction (PCA)
        if self.dimensionality_reducer:
            df_out = self.dimensionality_reducer.transform(df_out)

        return df_out

    def transform_target(self, series: pd.Series) -> pd.Series:
        """Transforms target labels using the fitted target encoder."""
        if not self.target_encoder:
            return series
        return self.target_encoder.transform(series)

    def save(self, file_path: Union[str, Path]) -> None:
        """Serializes the pipeline object to disk via joblib."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "PreprocessingPipeline":
        """Loads a serialized pipeline object from disk."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Serialized pipeline not found at: {path}")
        return joblib.load(path)
