"""Unit tests for data quality detection tools."""

import numpy as np
import pandas as pd
from app.tools.quality_analysis import (
    detect_missing_values,
    detect_duplicates,
    detect_inconsistent_categories,
    detect_class_imbalance,
    detect_target_leakage,
    run_quality_analysis
)


def test_detect_missing_and_duplicates():
    df = pd.DataFrame({
        "A": [1, 2, np.nan, 4, 1],
        "B": ["yes", "no", "yes", "no", "yes"],
        "C": [10, 20, 30, 40, 10]
    })
    missing = detect_missing_values(df)
    assert missing["has_missing"] is True
    assert missing["total_missing"] == 1
    assert "A" in missing["affected_columns"]

    dups = detect_duplicates(df)
    assert dups["has_duplicates"] is True
    assert dups["duplicate_count"] == 1


def test_detect_inconsistent_categories():
    df = pd.DataFrame({
        "status": ["YES", "yes", "Yes", "NO", "no"]
    })
    inc = detect_inconsistent_categories(df)
    assert inc["has_inconsistencies"] is True
    assert "status" in inc["inconsistent_columns"]


def test_detect_class_imbalance():
    df = pd.DataFrame({
        "target": [0] * 90 + [1] * 10
    })
    imb = detect_class_imbalance(df, target_column="target")
    assert imb["is_imbalanced"] is True
    assert imb["minority_ratio"] == 0.10


def test_detect_target_leakage():
    target = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    df = pd.DataFrame({
        "perfect_leak": target,
        "noisy_feat": np.random.rand(10),
        "target": ["NO" if t == 0 else "YES" for t in target]
    })
    leakage = detect_target_leakage(df, target_column="target", threshold=0.95)
    assert len(leakage) == 1
    assert leakage[0]["feature"] == "perfect_leak"
    assert leakage[0]["correlation_with_target"] >= 0.99
