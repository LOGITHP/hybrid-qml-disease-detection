"""Deterministic feature selection tools with quantum-aligned feature budgeting."""

from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif, f_classif
from sklearn.ensemble import RandomForestClassifier

from ..schemas.features import FeatureScore, FeatureSelectionResult


class FeatureSelector:
    """Selects top K features fitted strictly on training data."""

    def __init__(self, method: str = "mutual_info", target_feature_count: Optional[int] = 4, random_state: int = 42):
        self.method = method.lower()
        self.target_feature_count = target_feature_count
        self.random_state = random_state
        self.selected_features: List[str] = []
        self.ranking: List[FeatureScore] = []
        self.fitted = False

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "FeatureSelector":
        """Calculates feature importance scores strictly on training partition."""
        feature_names = list(X_train.columns)
        if not feature_names:
            raise ValueError("Cannot perform feature selection on empty feature set.")

        # Ensure all columns are numeric
        X_num = X_train.select_dtypes(include=[np.number])
        if X_num.shape[1] != X_train.shape[1]:
            diff = set(X_train.columns) - set(X_num.columns)
            raise ValueError(f"Feature selection requires numeric features. Unencoded categorical columns found: {diff}")

        if self.method in ["mutual_info", "auto"]:
            scores = mutual_info_classif(X_num, y_train, random_state=self.random_state)
        elif self.method in ["f_classif", "anova"]:
            scores, _ = f_classif(X_num, y_train)
            scores = np.nan_to_num(scores, nan=0.0)
        elif self.method in ["random_forest", "rf"]:
            rf = RandomForestClassifier(n_estimators=100, random_state=self.random_state)
            rf.fit(X_num, y_train)
            scores = rf.feature_importances_
        else:
            raise ValueError(f"Unsupported feature selection method '{self.method}'. Choose 'mutual_info', 'f_classif', or 'random_forest'.")

        # Normalize scores to 0-1 range for uniform comparison
        max_s = float(np.max(scores)) if len(scores) > 0 and np.max(scores) > 0 else 1.0
        norm_scores = [float(s / max_s) for s in scores]

        # Rank features descending by score
        paired = sorted(zip(feature_names, norm_scores), key=lambda x: x[1], reverse=True)
        self.ranking = [
            FeatureScore(feature_name=name, score=round(score, 4), rank=idx + 1)
            for idx, (name, score) in enumerate(paired)
        ]

        if self.target_feature_count and self.target_feature_count < len(feature_names):
            self.selected_features = [item.feature_name for item in self.ranking[:self.target_feature_count]]
        else:
            self.selected_features = feature_names

        self.fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Subsets dataframe to selected features."""
        if not self.fitted:
            raise ValueError("FeatureSelector must be fitted on training data before transform.")
        return X[self.selected_features].copy()


def select_features(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: Optional[pd.DataFrame] = None,
    X_test: Optional[pd.DataFrame] = None,
    method: str = "mutual_info",
    target_feature_count: Optional[int] = 4,
    random_state: int = 42
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame], FeatureSelectionResult, FeatureSelector]:
    """Fits feature selection on train and filters val and test splits."""
    selector = FeatureSelector(
        method=method,
        target_feature_count=target_feature_count,
        random_state=random_state
    )
    selector.fit(X_train, y_train)

    t_train = selector.transform(X_train)
    t_val = selector.transform(X_val) if X_val is not None else None
    t_test = selector.transform(X_test) if X_test is not None else None

    result = FeatureSelectionResult(
        status="success",
        method=selector.method,
        target_feature_count=target_feature_count,
        input_feature_count=len(X_train.columns),
        selected_feature_count=len(selector.selected_features),
        selected_features=selector.selected_features,
        ranking=selector.ranking,
        fitted_on="train"
    )
    return t_train, t_val, t_test, result, selector
