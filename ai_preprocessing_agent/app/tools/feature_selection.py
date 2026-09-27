"""Deterministic feature selection tools with composite screening and SFS optimization."""

from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif, f_classif
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import cross_val_score

from ..schemas.features import FeatureScore, FeatureSelectionResult


class FeatureSelector:
    """Selects top K features fitted strictly on training data using multi-metric or SFS criteria."""

    def __init__(self, method: str = "sfs", target_feature_count: Optional[int] = 4, random_state: int = 42):
        self.method = method.lower()
        self.target_feature_count = target_feature_count
        self.random_state = random_state
        self.selected_features: List[str] = []
        self.ranking: List[FeatureScore] = []
        self.candidate_pool: List[str] = []
        self.fitted = False

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None
    ) -> "FeatureSelector":
        """Calculates feature scores and selects optimal subset."""
        feature_names = list(X_train.columns)
        if not feature_names:
            raise ValueError("Cannot perform feature selection on empty feature set.")

        X_num = X_train.select_dtypes(include=[np.number])
        if X_num.shape[1] != X_train.shape[1]:
            diff = set(X_train.columns) - set(X_num.columns)
            raise ValueError(f"Feature selection requires numeric features. Unencoded categorical columns found: {diff}")

        # Compute individual metrics
        mi_scores = mutual_info_classif(X_num, y_train, random_state=self.random_state)
        f_scores, _ = f_classif(X_num, y_train)
        f_scores = np.nan_to_num(f_scores, nan=0.0)

        rf = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=self.random_state)
        rf.fit(X_num, y_train)
        rf_scores = rf.feature_importances_

        # Rank metrics (1 is highest)
        rank_mi = pd.Series(mi_scores).rank(ascending=False, method="min").values
        rank_f = pd.Series(f_scores).rank(ascending=False, method="min").values
        rank_rf = pd.Series(rf_scores).rank(ascending=False, method="min").values

        composite_scores = (rank_mi + rank_f + rank_rf) / 3.0

        if self.method in ["mutual_info", "mi"]:
            primary_scores = mi_scores
            max_s = float(np.max(primary_scores)) if len(primary_scores) > 0 and np.max(primary_scores) > 0 else 1.0
            norm_scores = [float(s / max_s) for s in primary_scores]
            paired = sorted(zip(feature_names, norm_scores), key=lambda x: x[1], reverse=True)
            self.ranking = [
                FeatureScore(feature_name=name, score=round(score, 4), rank=idx + 1)
                for idx, (name, score) in enumerate(paired)
            ]
            k = self.target_feature_count or len(feature_names)
            self.selected_features = [item.feature_name for item in self.ranking[:k]]

        elif self.method in ["f_classif", "anova"]:
            primary_scores = f_scores
            max_s = float(np.max(primary_scores)) if len(primary_scores) > 0 and np.max(primary_scores) > 0 else 1.0
            norm_scores = [float(s / max_s) for s in primary_scores]
            paired = sorted(zip(feature_names, norm_scores), key=lambda x: x[1], reverse=True)
            self.ranking = [
                FeatureScore(feature_name=name, score=round(score, 4), rank=idx + 1)
                for idx, (name, score) in enumerate(paired)
            ]
            k = self.target_feature_count or len(feature_names)
            self.selected_features = [item.feature_name for item in self.ranking[:k]]

        elif self.method in ["composite", "multi_metric"]:
            # Sort by composite rank ascending (lowest rank number = best)
            paired = sorted(zip(feature_names, composite_scores), key=lambda x: x[1], reverse=False)
            max_c = float(np.max(composite_scores)) if len(composite_scores) > 0 else 1.0
            self.ranking = [
                FeatureScore(feature_name=name, score=round(1.0 - (comp / max_c), 4), rank=idx + 1)
                for idx, (name, comp) in enumerate(paired)
            ]
            k = self.target_feature_count or len(feature_names)
            self.selected_features = [item.feature_name for item in self.ranking[:k]]

        elif self.method in ["sfs", "auto", "sequential"]:
            # Step 1: Form candidate shortlist using composite ranking
            paired = sorted(zip(feature_names, composite_scores), key=lambda x: x[1], reverse=False)
            max_c = float(np.max(composite_scores)) if len(composite_scores) > 0 else 1.0
            self.ranking = [
                FeatureScore(feature_name=name, score=round(1.0 - (comp / max_c), 4), rank=idx + 1)
                for idx, (name, comp) in enumerate(paired)
            ]

            pool_size = min(max(8, (self.target_feature_count or 4) + 4), len(feature_names))
            candidate_pool = [item.feature_name for item in self.ranking[:pool_size]]
            self.candidate_pool = candidate_pool

            # Step 2: Sequential Forward Selection targeting target_feature_count
            k = self.target_feature_count or min(4, len(candidate_pool))
            selected: List[str] = []
            remaining = list(candidate_pool)

            for _ in range(k):
                best_cand = None
                best_score = -1.0
                for cand in remaining:
                    trial = selected + [cand]
                    clf = LogisticRegression(random_state=self.random_state, solver="lbfgs", max_iter=200)

                    if X_val is not None and y_val is not None and len(X_val) > 0:
                        clf.fit(X_num[trial], y_train)
                        val_pred = clf.predict(X_val[trial])
                        score = float(balanced_accuracy_score(y_val, val_pred))
                    else:
                        cv_scores = cross_val_score(clf, X_num[trial], y_train, cv=5, scoring="balanced_accuracy")
                        score = float(np.mean(cv_scores))

                    if score > best_score:
                        best_score = score
                        best_cand = cand

                if best_cand:
                    selected.append(best_cand)
                    remaining.remove(best_cand)
                else:
                    break

            self.selected_features = selected
        else:
            raise ValueError(f"Unsupported feature selection method '{self.method}'. Choose 'sfs', 'composite', 'mutual_info', or 'f_classif'.")

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
    y_val: Optional[pd.Series] = None,
    method: str = "sfs",
    target_feature_count: Optional[int] = 4,
    random_state: int = 42
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame], FeatureSelectionResult, FeatureSelector]:
    """Fits feature selection on train and filters val and test splits."""
    selector = FeatureSelector(
        method=method,
        target_feature_count=target_feature_count,
        random_state=random_state
    )
    selector.fit(X_train, y_train, X_val=X_val, y_val=y_val)

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
