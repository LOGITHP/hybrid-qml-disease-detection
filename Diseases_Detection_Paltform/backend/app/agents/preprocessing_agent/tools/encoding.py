"""Deterministic categorical encoding tools fitted strictly on training data."""

from typing import Tuple, Dict, Any, List, Optional
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, LabelEncoder


class CategoricalEncoder:
    """Encoder fitted strictly on training split with consistent alignment for val/test."""

    def __init__(self, method: str = "one_hot", drop_first: bool = False):
        self.method = method
        self.drop_first = drop_first
        self.encoder = None
        self.encoded_feature_names: List[str] = []
        self.categorical_cols: List[str] = []
        self.fitted = False

    def fit(self, df_train: pd.DataFrame, columns: Optional[List[str]] = None) -> "CategoricalEncoder":
        """Fits encoder on categorical columns of the training set."""
        if columns is None:
            self.categorical_cols = list(df_train.select_dtypes(include=["object", "string", "category"]).columns)
        else:
            self.categorical_cols = [c for c in columns if c in df_train.columns]

        if not self.categorical_cols:
            self.fitted = True
            return self

        if self.method == "one_hot":
            self.encoder = OneHotEncoder(
                sparse_output=False,
                handle_unknown="ignore",
                drop="first" if self.drop_first else None
            )
            self.encoder.fit(df_train[self.categorical_cols])
            self.encoded_feature_names = list(self.encoder.get_feature_names_out(self.categorical_cols))
        elif self.method == "ordinal":
            self.encoder = OrdinalEncoder(
                handle_unknown="use_encoded_value",
                unknown_value=-1
            )
            self.encoder.fit(df_train[self.categorical_cols])
            self.encoded_feature_names = self.categorical_cols
        else:
            raise ValueError(f"Unsupported encoding method '{self.method}'. Use 'one_hot' or 'ordinal'.")

        self.fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies fitted encoding to a DataFrame."""
        if not self.fitted:
            raise ValueError("CategoricalEncoder must be fitted on training data before transform.")

        if not self.categorical_cols or self.encoder is None:
            return df.copy()

        # Non-categorical pass-through columns
        passthrough_cols = [c for c in df.columns if c not in self.categorical_cols]
        df_passthrough = df[passthrough_cols].reset_index(drop=True)

        encoded_arr = self.encoder.transform(df[self.categorical_cols])
        df_encoded = pd.DataFrame(encoded_arr, columns=self.encoded_feature_names)

        return pd.concat([df_passthrough, df_encoded], axis=1)


class TargetLabelEncoder:
    """Encodes classification target strings into integer labels (e.g. YES->1, NO->0)."""

    def __init__(self):
        self.mapping: Dict[Any, int] = {}
        self.inverse_mapping: Dict[int, Any] = {}
        self.classes: List[str] = []

    def fit(self, series_train: pd.Series) -> "TargetLabelEncoder":
        """Identifies classes and assigns canonical binary or multiclass labels."""
        unique_vals = list(series_train.dropna().unique())
        # Canonical sorting: if NO/YES present, ensure NO=0, YES=1
        if set(str(v).upper() for v in unique_vals) == {"NO", "YES"}:
            for v in unique_vals:
                if str(v).upper() == "NO":
                    self.mapping[v] = 0
                else:
                    self.mapping[v] = 1
        elif set(str(v).lower() for v in unique_vals) in [{"0", "1"}, {"false", "true"}]:
            for v in unique_vals:
                clean = str(v).lower()
                self.mapping[v] = 0 if clean in ["0", "false"] else 1
        else:
            sorted_vals = sorted(unique_vals, key=lambda x: str(x))
            self.mapping = {v: idx for idx, v in enumerate(sorted_vals)}

        self.inverse_mapping = {v: k for k, v in self.mapping.items()}
        self.classes = [str(k) for k in self.mapping.keys()]
        return self

    def transform(self, series: pd.Series) -> pd.Series:
        """Transforms target series to integer labels."""
        transformed = series.map(self.mapping)
        if transformed.isnull().any():
            unmapped = series[transformed.isnull()].unique()
            raise ValueError(f"Unseen target classes in evaluation set: {unmapped}")
        return transformed.astype(int)


def encode_categorical_features(
    train_df: pd.DataFrame,
    val_df: Optional[pd.DataFrame] = None,
    test_df: Optional[pd.DataFrame] = None,
    columns: Optional[List[str]] = None,
    method: str = "one_hot"
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame], Dict[str, Any], CategoricalEncoder]:
    """Fits categorical encoding strictly on train split and transforms all splits."""
    encoder = CategoricalEncoder(method=method)
    encoder.fit(train_df, columns=columns)

    t_train = encoder.transform(train_df)
    t_val = encoder.transform(val_df) if val_df is not None else None
    t_test = encoder.transform(test_df) if test_df is not None else None

    report = {
        "operation": "encode_categorical_features",
        "method": method,
        "input_categorical_columns": encoder.categorical_cols,
        "generated_columns": encoder.encoded_feature_names,
        "fitted_on": "train",
        "status": "success"
    }
    return t_train, t_val, t_test, report, encoder
