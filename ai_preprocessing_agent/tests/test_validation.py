"""Unit tests for post-processing validation and leakage detection."""

import numpy as np
import pandas as pd
from app.tools.validation import validate_processed_dataset


def test_validate_processed_dataset_clean():
    X_train = pd.DataFrame({"f1": [0.1, 0.2, 0.3], "f2": [0.4, 0.5, 0.6]})
    X_val = pd.DataFrame({"f1": [0.2], "f2": [0.5]})
    X_test = pd.DataFrame({"f1": [0.3], "f2": [0.6]})
    y_train = pd.Series([0, 1, 0])
    y_val = pd.Series([1])
    y_test = pd.Series([0])

    res = validate_processed_dataset(
        X_train, X_val, X_test,
        y_train, y_val, y_test,
        target_feature_count=2,
        target_name="target"
    )
    assert res.passed is True
    assert res.status == "passed"
    assert res.leakage_detected is False


def test_validate_target_leakage_detected():
    X_train = pd.DataFrame({"f1": [0.1, 0.2], "target": [0, 1]})
    y_train = pd.Series([0, 1])

    res = validate_processed_dataset(
        X_train, None, None,
        y_train, None, None,
        target_name="target"
    )
    assert res.passed is False
    assert res.leakage_detected is True
    assert any(e.code == "VAL_TARGET_LEAKAGE" for e in res.errors)
