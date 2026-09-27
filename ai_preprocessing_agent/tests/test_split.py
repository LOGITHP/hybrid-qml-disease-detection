"""Unit tests for stratified dataset splitting."""

import pandas as pd
from app.tools.splitting import split_dataset


def test_stratified_split():
    df = pd.DataFrame({
        "feat1": list(range(100)),
        "feat2": list(range(100, 200)),
        "target": [0] * 70 + [1] * 30
    })

    X_train, X_val, X_test, y_train, y_val, y_test, split_res = split_dataset(
        df,
        target_column="target",
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        stratify=True,
        random_state=42
    )

    assert len(X_train) in [69, 70]
    assert len(X_val) in [15, 16]
    assert len(X_test) == 15
    assert "target" not in X_train.columns

    # Check stratification preservation
    train_ratio_pos = (y_train == 1).mean()
    val_ratio_pos = (y_val == 1).mean()
    test_ratio_pos = (y_test == 1).mean()

    assert abs(train_ratio_pos - 0.30) < 0.05
    assert abs(val_ratio_pos - 0.30) < 0.08
    assert abs(test_ratio_pos - 0.30) < 0.08
