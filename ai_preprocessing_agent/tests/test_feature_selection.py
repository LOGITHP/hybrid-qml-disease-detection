"""Unit tests for feature selection and quantum feature budgeting."""

import numpy as np
import pandas as pd
from app.tools.feature_selection import select_features


def test_select_4_features_quantum():
    np.random.seed(42)
    n = 100
    y = pd.Series(np.random.choice([0, 1], size=n))

    # Features: f1 and f2 strongly correlated with y, f3 and f4 moderately, others random noise
    X = pd.DataFrame({
        "f1": y + np.random.normal(0, 0.1, size=n),
        "f2": y * 2 + np.random.normal(0, 0.2, size=n),
        "f3": y * 0.5 + np.random.normal(0, 0.3, size=n),
        "f4": y * -1 + np.random.normal(0, 0.3, size=n),
        "noise1": np.random.normal(0, 1, size=n),
        "noise2": np.random.normal(0, 1, size=n),
        "noise3": np.random.normal(0, 1, size=n),
        "noise4": np.random.normal(0, 1, size=n)
    })

    t_train, _, _, res, selector = select_features(X, y, target_feature_count=4, method="mutual_info")

    assert res.selected_feature_count == 4
    assert set(res.selected_features).issubset(set(X.columns))
    assert "f1" in res.selected_features
    assert "f2" in res.selected_features
    assert t_train.shape[1] == 4
