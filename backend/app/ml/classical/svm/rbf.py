"""Support Vector Machine (Radial Basis Function Kernel) model implementation."""

from typing import Any, Dict
import numpy as np
from sklearn.svm import SVC
from app.interfaces.model import IModel


class SVMRBFModel(IModel):
    """RBF Kernel Support Vector Classifier."""

    def __init__(self, C: float = 1.0, gamma: str = "scale", random_state: int = 42):
        self.C = C
        self.gamma = gamma
        self.random_state = random_state
        self._clf = SVC(
            kernel="rbf",
            C=self.C,
            gamma=self.gamma,
            probability=True,
            random_state=self.random_state,
        )

    @property
    def model_type(self) -> str:
        return "svm_rbf"

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs: Any) -> "SVMRBFModel":
        self._clf.fit(X, y)
        return self

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        if threshold == 0.5:
            return self._clf.predict(X)
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(int)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._clf.predict_proba(X)[:, 1]

    def get_params(self) -> Dict[str, Any]:
        return {"C": self.C, "gamma": self.gamma, "random_state": self.random_state, "kernel": "rbf"}
