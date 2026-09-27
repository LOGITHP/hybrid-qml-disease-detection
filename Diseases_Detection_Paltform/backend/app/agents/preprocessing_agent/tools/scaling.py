"""Deterministic numerical feature scaling tools fitted strictly on training data."""

from typing import Tuple, Dict, Any, List, Optional
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler


class NumericalScaler:
    """Scales numerical features with strict fit-on-train guarantees."""

    def __init__(self, method: str = "minmax"):
        self.method = method.lower()
        self.scaler = None
        self.columns_to_scale: List[str] = []
        self.fitted = False

    def fit(self, df_train: pd.DataFrame, columns: Optional[List[str]] = None) -> "NumericalScaler":
        """Fits scaler strictly on numerical columns of training data."""
        if columns is None:
            self.columns_to_scale = list(df_train.select_dtypes(include=["float64", "int64", "float32", "int32"]).columns)
        else:
            self.columns_to_scale = [c for c in columns if c in df_train.columns and pd.api.types.is_numeric_dtype(df_train[c])]

        if not self.columns_to_scale:
            self.fitted = True
            return self

        if self.method in ["minmax", "min_max"]:
            self.scaler = MinMaxScaler(feature_range=(0, 1))
        elif self.method in ["standard", "standardscaler"]:
            self.scaler = StandardScaler()
        elif self.method in ["robust", "robustscaler"]:
            self.scaler = RobustScaler()
        else:
            raise ValueError(f"Unsupported scaling method '{self.method}'. Choose 'minmax', 'standard', or 'robust'.")

        self.scaler.fit(df_train[self.columns_to_scale])
        self.fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies fitted scaling transformations."""
        if not self.fitted:
            raise ValueError("NumericalScaler must be fitted on training data before transform.")

        if not self.columns_to_scale or self.scaler is None:
            return df.copy()

        df_out = df.copy()
        scaled_vals = self.scaler.transform(df_out[self.columns_to_scale])
        for idx, col in enumerate(self.columns_to_scale):
            df_out[col] = scaled_vals[:, idx]
        return df_out


def scale_numerical_features(
    train_df: pd.DataFrame,
    val_df: Optional[pd.DataFrame] = None,
    test_df: Optional[pd.DataFrame] = None,
    columns: Optional[List[str]] = None,
    method: str = "minmax"
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame], Dict[str, Any], NumericalScaler]:
    """Fits numerical scaler on training split and transforms all partitions."""
    scaler = NumericalScaler(method=method)
    scaler.fit(train_df, columns=columns)

    t_train = scaler.transform(train_df)
    t_val = scaler.transform(val_df) if val_df is not None else None
    t_test = scaler.transform(test_df) if test_df is not None else None

    report = {
        "operation": "scale_numerical_features",
        "method": scaler.method,
        "scaled_columns": scaler.columns_to_scale,
        "fitted_on": "train",
        "status": "success"
    }
    return t_train, t_val, t_test, report, scaler
