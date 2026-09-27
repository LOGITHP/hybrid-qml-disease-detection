"""Unit tests for categorical encoding and target mapping."""

import pandas as pd
from app.tools.encoding import encode_categorical_features, TargetLabelEncoder


def test_target_label_encoder():
    s_train = pd.Series(["NO", "YES", "NO", "YES"])
    s_val = pd.Series(["YES", "NO"])

    encoder = TargetLabelEncoder()
    encoder.fit(s_train)

    enc_train = encoder.transform(s_train)
    enc_val = encoder.transform(s_val)

    assert list(enc_train) == [0, 1, 0, 1]
    assert list(enc_val) == [1, 0]


def test_encode_categorical_features_one_hot():
    train_df = pd.DataFrame({"color": ["red", "blue", "red"], "val": [1, 2, 3]})
    val_df = pd.DataFrame({"color": ["blue", "blue"], "val": [4, 5]})

    t_train, t_val, _, rep, encoder = encode_categorical_features(train_df, val_df, method="one_hot")

    assert "color_red" in t_train.columns
    assert "color_blue" in t_train.columns
    assert list(t_train.columns) == list(t_val.columns)
    assert t_val["color_red"].sum() == 0
    assert t_val["color_blue"].sum() == 2
