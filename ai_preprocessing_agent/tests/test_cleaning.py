"""Unit tests for cleaning tools and train-only missing value imputation."""

import numpy as np
import pandas as pd
from app.tools.cleaning import remove_duplicates, clean_categorical_values, handle_missing_values


def test_remove_duplicates():
    df = pd.DataFrame({
        "A": [1, 2, 2, 3],
        "B": ["a", "b", "b", "c"]
    })
    cleaned, report = remove_duplicates(df)
    assert len(cleaned) == 3
    assert report["removed_count"] == 1


def test_clean_categorical_values():
    df = pd.DataFrame({
        "text": ["  yes ", "NO  ", "yes", "no "]
    })
    cleaned, report = clean_categorical_values(df)
    assert list(cleaned["text"]) == ["YES", "NO", "YES", "NO"]
    assert "text" in report["columns_modified"]


def test_handle_missing_values_fit_on_train():
    train_df = pd.DataFrame({"A": [10.0, 20.0, np.nan, 40.0], "B": ["X", "Y", "X", np.nan]})
    val_df = pd.DataFrame({"A": [np.nan, 30.0], "B": [np.nan, "Y"]})

    # Train median for A is median of [10, 20, 40] = 20.0
    # Train mode for B is "X"
    t_train, t_val, _, rep, imputer = handle_missing_values(train_df, val_df, strategy_num="median", strategy_cat="mode")

    assert t_train["A"].iloc[2] == 20.0
    assert t_train["B"].iloc[3] == "X"
    assert t_val["A"].iloc[0] == 20.0
    assert t_val["B"].iloc[0] == "X"
    assert rep["fitted_on"] == "train"
