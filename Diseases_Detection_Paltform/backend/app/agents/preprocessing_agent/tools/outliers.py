"""Deterministic outlier handling tools with train-fitted boundaries."""

from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import pandas as pd


class OutlierHandler:
    """Handles outliers via retention or train-fitted IQR clipping."""

    def __init__(self, strategy: str = "retain", factor: float = 1.5):
        self.strategy = strategy.lower()
        self.factor = factor
        self.bounds: Dict[str, Tuple[float, float]] = {}
        self.fitted = False

    def fit(self, df_train: pd.DataFrame, columns: Optional[List[str]] = None) -> "OutlierHandler":
        """Calculates outlier boundaries strictly on training split."""
        if columns is None:
            # Only consider continuous numerical columns (> 5 unique values)
            cols = [c for c in df_train.select_dtypes(include=[np.number]).columns if df_train[c].nunique() > 5]
        else:
            cols = [c for c in columns if c in df_train.columns and pd.api.types.is_numeric_dtype(df_train[c])]

        self.bounds = {}
        if self.strategy == "clip":
            for c in cols:
                series = df_train[c].dropna()
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower = float(q1 - self.factor * iqr)
                    upper = float(q3 + self.factor * iqr)
                    self.bounds[c] = (lower, upper)

        self.fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies outlier strategy to dataframe."""
        if not self.fitted:
            raise ValueError("OutlierHandler must be fitted on training data before transform.")

        if self.strategy == "retain" or not self.bounds:
            return df.copy()

        df_out = df.copy()
        if self.strategy == "clip":
            for col, (lower, upper) in self.bounds.items():
                if col in df_out.columns:
                    df_out[col] = df_out[col].clip(lower=lower, upper=upper)

        return df_out


def handle_outliers(
    train_df: pd.DataFrame,
    val_df: Optional[pd.DataFrame] = None,
    test_df: Optional[pd.DataFrame] = None,
    columns: Optional[List[str]] = None,
    strategy: str = "retain"
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame], Dict[str, Any], OutlierHandler]:
    """Handles outliers based on configuration strategy."""
    handler = OutlierHandler(strategy=strategy)
    handler.fit(train_df, columns=columns)

    t_train = handler.transform(train_df)
    t_val = handler.transform(val_df) if val_df is not None else None
    t_test = handler.transform(test_df) if test_df is not None else None

    report = {
        "operation": "handle_outliers",
        "strategy": strategy,
        "clipping_bounds": handler.bounds,
        "fitted_on": "train",
        "status": "success"
    }
    return t_train, t_val, t_test, report, handler
