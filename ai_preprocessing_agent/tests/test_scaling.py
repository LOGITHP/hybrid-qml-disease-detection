"""Unit tests for numerical scaling fitted strictly on train data."""

import pandas as pd
from app.tools.scaling import scale_numerical_features


def test_scale_numerical_minmax():
    train_df = pd.DataFrame({"age": [20.0, 40.0, 60.0]})
    val_df = pd.DataFrame({"age": [40.0, 80.0]})  # 80 is beyond train max of 60

    t_train, t_val, _, rep, scaler = scale_numerical_features(train_df, val_df, method="minmax")

    assert t_train["age"].min() == 0.0
    assert t_train["age"].max() == 1.0
    assert t_val["age"].iloc[0] == 0.5  # 40 -> 0.5
    assert t_val["age"].iloc[1] == 1.5  # 80 -> (80-20)/(60-20) = 1.5 (Strict train-fit proof!)
    assert rep["fitted_on"] == "train"
