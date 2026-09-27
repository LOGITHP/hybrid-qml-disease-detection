"""Deterministic dataset splitting with stratified multi-partition support."""

from typing import Tuple, Dict, Any, Optional
import pandas as pd
from sklearn.model_selection import train_test_split

from ..schemas.result import DatasetSplitResult


def split_dataset(
    df: pd.DataFrame,
    target_column: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
    stratify: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series, DatasetSplitResult]:
    """Splits dataset into stratified train, validation, and test subsets.

    Args:
        df: Input cleaned DataFrame
        target_column: Name of the target column
        train_ratio: Proportion for training (default 0.70)
        val_ratio: Proportion for validation (default 0.15)
        test_ratio: Proportion for test (default 0.15)
        random_state: Reproducibility seed
        stratify: Whether to preserve class proportions

    Returns:
        Tuple of (X_train, X_val, X_test, y_train, y_val, y_test, DatasetSplitResult)
    """
    total_ratio = train_ratio + val_ratio + test_ratio
    if abs(total_ratio - 1.0) > 1e-4:
        raise ValueError(f"Split ratios must sum to 1.0, got: {total_ratio}")

    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset columns: {list(df.columns)}")

    X = df.drop(columns=[target_column]).copy()
    y = df[target_column].copy()

    stratify_target = y if stratify and y.nunique() <= 20 else None

    # Step 1: Split off test set
    test_size = test_ratio
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_target
    )

    # Step 2: Split remaining into train and validation
    val_relative_size = val_ratio / (train_ratio + val_ratio)
    stratify_temp = y_temp if stratify and y_temp.nunique() <= 20 else None

    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp,
        test_size=val_relative_size,
        random_state=random_state,
        stratify=stratify_temp
    )

    # Audit class distribution
    train_dist = {str(k): int(v) for k, v in y_train.value_counts().items()}
    val_dist = {str(k): int(v) for k, v in y_val.value_counts().items()}
    test_dist = {str(k): int(v) for k, v in y_test.value_counts().items()}

    split_result = DatasetSplitResult(
        status="success",
        random_state=random_state,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        train_samples=len(X_train),
        val_samples=len(X_val),
        test_samples=len(X_test),
        target_column=target_column,
        stratified=stratify_target is not None,
        train_class_distribution=train_dist,
        val_class_distribution=val_dist,
        test_class_distribution=test_dist
    )

    return (
        X_train.reset_index(drop=True),
        X_val.reset_index(drop=True),
        X_test.reset_index(drop=True),
        y_train.reset_index(drop=True),
        y_val.reset_index(drop=True),
        y_test.reset_index(drop=True),
        split_result
    )
