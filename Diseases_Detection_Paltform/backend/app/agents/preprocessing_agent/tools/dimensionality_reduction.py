"""Deterministic dimensionality reduction tools via PCA."""

from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from ..schemas.features import DimensionalityReductionResult


class DimensionalityReducer:
    """PCA dimensionality reducer with fit-on-train guarantees."""

    def __init__(self, n_components: int = 4, random_state: int = 42):
        self.n_components = n_components
        self.random_state = random_state
        self.pca = None
        self.feature_names_out: List[str] = []
        self.explained_variance_ratio: List[float] = []
        self.fitted = False

    def fit(self, X_train: pd.DataFrame) -> "DimensionalityReducer":
        """Fits PCA strictly on training dataframe."""
        n_features = X_train.shape[1]
        n_comp = min(self.n_components, n_features)

        self.pca = PCA(n_components=n_comp, random_state=self.random_state)
        self.pca.fit(X_train)

        self.explained_variance_ratio = [float(round(r, 4)) for r in self.pca.explained_variance_ratio_]
        self.feature_names_out = [f"PC_{i+1}" for i in range(n_comp)]
        self.fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Projects dataframe into principal component subspace."""
        if not self.fitted or self.pca is None:
            raise ValueError("DimensionalityReducer must be fitted on training data before transform.")
        transformed = self.pca.transform(X)
        return pd.DataFrame(transformed, columns=self.feature_names_out, index=X.index)


def reduce_dimensions(
    X_train: pd.DataFrame,
    X_val: Optional[pd.DataFrame] = None,
    X_test: Optional[pd.DataFrame] = None,
    enabled: bool = False,
    n_components: int = 4,
    random_state: int = 42
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame], DimensionalityReductionResult, Optional[DimensionalityReducer]]:
    """Applies PCA dimensionality reduction if enabled."""
    if not enabled:
        result = DimensionalityReductionResult(
            status="success",
            applied=False,
            method="pca",
            n_components=None,
            input_dimensions=X_train.shape[1],
            output_dimensions=X_train.shape[1],
            explained_variance_ratio=[],
            total_explained_variance=0.0,
            fitted_on="train"
        )
        return X_train.copy(), X_val.copy() if X_val is not None else None, X_test.copy() if X_test is not None else None, result, None

    reducer = DimensionalityReducer(n_components=n_components, random_state=random_state)
    reducer.fit(X_train)

    t_train = reducer.transform(X_train)
    t_val = reducer.transform(X_val) if X_val is not None else None
    t_test = reducer.transform(X_test) if X_test is not None else None

    total_var = float(round(sum(reducer.explained_variance_ratio), 4))
    result = DimensionalityReductionResult(
        status="success",
        applied=True,
        method="pca",
        n_components=len(reducer.feature_names_out),
        input_dimensions=X_train.shape[1],
        output_dimensions=len(reducer.feature_names_out),
        explained_variance_ratio=reducer.explained_variance_ratio,
        total_explained_variance=total_var,
        fitted_on="train"
    )
    return t_train, t_val, t_test, result, reducer
