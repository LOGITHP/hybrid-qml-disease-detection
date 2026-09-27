"""Support Vector Machine models."""

from app.ml.classical.svm.linear import SVMLinearModel
from app.ml.classical.svm.rbf import SVMRBFModel

__all__ = ["SVMLinearModel", "SVMRBFModel"]
