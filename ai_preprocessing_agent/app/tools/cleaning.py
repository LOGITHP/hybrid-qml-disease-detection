"""Deterministic dataset cleaning tools for duplicates, whitespace, and missing values."""

from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import pandas as pd


def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Removes duplicate rows from the dataset.

    Args:
        df: Input DataFrame

    Returns:
        Tuple of (Cleaned DataFrame, Audit Report)
    """
    initial_rows = len(df)
    df_cleaned = df.drop_duplicates().copy().reset_index(drop=True)
    final_rows = len(df_cleaned)
    removed = initial_rows - final_rows

    report = {
        "operation": "remove_duplicates",
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "removed_count": removed,
        "status": "success"
    }
    return df_cleaned, report


def clean_categorical_values(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Normalizes string categorical values by trimming whitespace and standardizing casing.

    Args:
        df: Input DataFrame
        columns: Optional list of columns to clean (defaults to all object/string columns)

    Returns:
        Tuple of (Cleaned DataFrame, Audit Report)
    """
    df_cleaned = df.copy()
    target_cols = columns or list(df_cleaned.select_dtypes(include=["object", "string"]).columns)
    modified_cols = []

    for col in target_cols:
        if col in df_cleaned.columns:
            # Strip whitespace
            cleaned_series = df_cleaned[col].astype(str).str.strip()
            # Standardize common yes/no tokens safely
            cleaned_series = cleaned_series.replace({
                "yes": "YES", "Yes": "YES", "y": "YES", "Y": "YES",
                "no": "NO", "No": "NO", "n": "NO", "N": "NO"
            })
            if not df_cleaned[col].equals(cleaned_series):
                df_cleaned[col] = cleaned_series
                modified_cols.append(col)

    report = {
        "operation": "clean_categorical_values",
        "columns_inspected": target_cols,
        "columns_modified": modified_cols,
        "status": "success"
    }
    return df_cleaned, report


class MissingValueImputer:
    """Stateful imputer ensuring stats are fitted ONLY on training data."""

    def __init__(self, strategy_num: str = "median", strategy_cat: str = "mode"):
        self.strategy_num = strategy_num
        self.strategy_cat = strategy_cat
        self.impute_values: Dict[str, Any] = {}
        self.fitted = False

    def fit(self, df_train: pd.DataFrame) -> "MissingValueImputer":
        """Calculates imputation parameters strictly on training dataframe."""
        self.impute_values = {}
        for col in df_train.columns:
            series = df_train[col]
            if pd.api.types.is_numeric_dtype(series):
                if self.strategy_num == "mean":
                    val = float(series.mean())
                else:
                    val = float(series.median())
                self.impute_values[col] = val
            else:
                mode_s = series.mode()
                val = str(mode_s.iloc[0]) if not mode_s.empty else "Unknown"
                self.impute_values[col] = val
        self.fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies fitted imputation values to a target dataframe."""
        if not self.fitted:
            raise ValueError("MissingValueImputer must be fitted on training data before transform.")
        df_out = df.copy()
        for col, val in self.impute_values.items():
            if col in df_out.columns and df_out[col].isnull().any():
                df_out[col] = df_out[col].fillna(val)
        return df_out


def handle_missing_values(
    train_df: pd.DataFrame,
    val_df: Optional[pd.DataFrame] = None,
    test_df: Optional[pd.DataFrame] = None,
    strategy_num: str = "median",
    strategy_cat: str = "mode"
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame], Dict[str, Any], MissingValueImputer]:
    """Fits missing value imputation on training split and transforms all partitions."""
    imputer = MissingValueImputer(strategy_num=strategy_num, strategy_cat=strategy_cat)
    imputer.fit(train_df)

    t_train = imputer.transform(train_df)
    t_val = imputer.transform(val_df) if val_df is not None else None
    t_test = imputer.transform(test_df) if test_df is not None else None

    report = {
        "operation": "handle_missing_values",
        "strategy_numerical": strategy_num,
        "strategy_categorical": strategy_cat,
        "fitted_on": "train",
        "imputed_columns": list(imputer.impute_values.keys()),
        "status": "success"
    }
    return t_train, t_val, t_test, report, imputer
