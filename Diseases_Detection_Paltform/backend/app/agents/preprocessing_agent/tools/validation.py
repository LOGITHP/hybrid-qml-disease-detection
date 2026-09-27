"""Deterministic dataset validation tools for leakage and integrity checks."""

from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd

from ..schemas.validation import ValidationErrorItem, ValidationWarningItem, ValidationResult


def validate_processed_dataset(
    X_train: pd.DataFrame,
    X_val: Optional[pd.DataFrame],
    X_test: Optional[pd.DataFrame],
    y_train: pd.Series,
    y_val: Optional[pd.Series],
    y_test: Optional[pd.Series],
    target_feature_count: Optional[int] = None,
    target_name: Optional[str] = None
) -> ValidationResult:
    """Rigorous post-processing validation for ML and Quantum readiness."""
    errors: List[ValidationErrorItem] = []
    warnings: List[ValidationWarningItem] = []
    checks: Dict[str, bool] = {}

    # Check 1: Missing values
    missing_train = int(X_train.isnull().sum().sum())
    missing_val = int(X_val.isnull().sum().sum()) if X_val is not None else 0
    missing_test = int(X_test.isnull().sum().sum()) if X_test is not None else 0
    total_missing = missing_train + missing_val + missing_test
    checks["no_missing_values"] = (total_missing == 0)
    if total_missing > 0:
        errors.append(ValidationErrorItem(
            code="VAL_MISSING_VALUES",
            stage="imputation",
            message=f"Detected remaining missing values: train={missing_train}, val={missing_val}, test={missing_test}.",
            recoverable=True,
            suggested_fix="Re-run missing value imputation with fallback strategy."
        ))

    # Check 2: All features must be numeric
    non_num_train = [c for c in X_train.columns if not pd.api.types.is_numeric_dtype(X_train[c])]
    checks["all_numeric_features"] = (len(non_num_train) == 0)
    if non_num_train:
        errors.append(ValidationErrorItem(
            code="VAL_NON_NUMERIC_FEATURES",
            stage="encoding",
            message=f"Unencoded categorical features found in feature set: {non_num_train}",
            recoverable=True,
            suggested_fix="Re-run categorical encoding on unencoded columns."
        ))

    # Check 3: Target leakage into X
    target_in_X = False
    if target_name:
        target_in_X = (target_name in X_train.columns)
    checks["target_excluded_from_features"] = not target_in_X
    if target_in_X:
        errors.append(ValidationErrorItem(
            code="VAL_TARGET_LEAKAGE",
            stage="feature_selection",
            message=f"Target column '{target_name}' was found in feature matrix X.",
            recoverable=True,
            suggested_fix="Drop target column from feature set."
        ))

    # Check 4: Feature count alignment (especially for Quantum 4-qubit VQC)
    actual_feature_count = X_train.shape[1]
    if target_feature_count is not None:
        count_match = (actual_feature_count == target_feature_count)
        checks["feature_count_matches_target"] = count_match
        if not count_match:
            errors.append(ValidationErrorItem(
                code="VAL_FEATURE_COUNT_MISMATCH",
                stage="feature_selection",
                message=f"Expected {target_feature_count} features for downstream model, got {actual_feature_count}.",
                recoverable=True,
                suggested_fix=f"Re-run feature selection with target_feature_count={target_feature_count}."
            ))
    else:
        checks["feature_count_matches_target"] = True

    # Check 5: Column name alignment across partitions
    if X_val is not None and list(X_train.columns) != list(X_val.columns):
        errors.append(ValidationErrorItem(
            code="VAL_COLUMN_MISMATCH_VAL",
            stage="splitting",
            message="Feature columns in X_val do not match X_train exactly.",
            recoverable=False
        ))
    if X_test is not None and list(X_train.columns) != list(X_test.columns):
        errors.append(ValidationErrorItem(
            code="VAL_COLUMN_MISMATCH_TEST",
            stage="splitting",
            message="Feature columns in X_test do not match X_train exactly.",
            recoverable=False
        ))
    checks["column_alignment"] = (len([e for e in errors if "COLUMN_MISMATCH" in e.code]) == 0)

    # Check 6: Infinite numbers
    inf_count = int(np.isinf(X_train.select_dtypes(include=[np.number])).sum().sum())
    checks["finite_values"] = (inf_count == 0)
    if inf_count > 0:
        errors.append(ValidationErrorItem(
            code="VAL_INFINITE_VALUES",
            stage="scaling",
            message=f"Found {inf_count} infinite values in X_train.",
            recoverable=True,
            suggested_fix="Apply clipping or robust scaling."
        ))

    # Check 7: Train-test overlap / duplicate leakage
    if X_test is not None:
        # Check intersection between train and test
        merged = pd.merge(X_train, X_test, how="inner")
        if len(merged) > 0:
            warnings.append(ValidationWarningItem(
                code="WARN_TRAIN_TEST_EXACT_MATCH",
                stage="data_leakage",
                message=f"Found {len(merged)} identical feature rows between train and test (common in discrete survey data)."
            ))

    passed = len(errors) == 0
    status = "passed" if passed else ("warning" if len(warnings) > 0 and len(errors) == 0 else "failed")

    return ValidationResult(
        status=status,
        passed=passed,
        errors=errors,
        warnings=warnings,
        checks=checks,
        leakage_detected=target_in_X,
        train_shape=[int(X_train.shape[0]), int(X_train.shape[1])],
        val_shape=[int(X_val.shape[0]), int(X_val.shape[1])] if X_val is not None else [],
        test_shape=[int(X_test.shape[0]), int(X_test.shape[1])] if X_test is not None else [],
        feature_count=actual_feature_count
    )
