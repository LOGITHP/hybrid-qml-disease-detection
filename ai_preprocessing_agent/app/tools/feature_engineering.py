"""Deterministic feature engineering tools."""

from typing import Tuple, Dict, Any, List, Optional
import pandas as pd
from ..schemas.features import FeatureEngineeringResult


def engineer_features(
    train_df: pd.DataFrame,
    val_df: Optional[pd.DataFrame] = None,
    test_df: Optional[pd.DataFrame] = None,
    enabled: bool = False,
    allow_interactions: bool = False
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame], FeatureEngineeringResult]:
    """Applies justified feature engineering or returns clean pass-through."""
    if not enabled:
        result = FeatureEngineeringResult(
            status="success",
            applied=False,
            transformations=[],
            new_features=[],
            rationale="No feature engineering applied (disabled by configuration)."
        )
        return train_df.copy(), val_df.copy() if val_df is not None else None, test_df.copy() if test_df is not None else None, result

    # When enabled, apply domain-neutral interaction terms if requested
    new_cols = []
    t_train = train_df.copy()
    t_val = val_df.copy() if val_df is not None else None
    t_test = test_df.copy() if test_df is not None else None

    # Example: symptom interaction score if relevant columns exist
    respiratory_cols = [c for c in ["COUGHING", "WHEEZING", "SHORTNESS_OF_BREATH"] if c in t_train.columns]
    if len(respiratory_cols) >= 2:
        col_name = "RESPIRATORY_SYMPTOM_COMPOSITE"
        t_train[col_name] = t_train[respiratory_cols].mean(axis=1)
        if t_val is not None:
            t_val[col_name] = t_val[respiratory_cols].mean(axis=1)
        if t_test is not None:
            t_test[col_name] = t_test[respiratory_cols].mean(axis=1)
        new_cols.append(col_name)

    result = FeatureEngineeringResult(
        status="success",
        applied=len(new_cols) > 0,
        transformations=[{"type": "composite_mean", "columns": respiratory_cols}] if new_cols else [],
        new_features=new_cols,
        rationale=f"Engineered {len(new_cols)} composite features based on symptom co-occurrence." if new_cols else "No feature engineering justified."
    )
    return t_train, t_val, t_test, result
