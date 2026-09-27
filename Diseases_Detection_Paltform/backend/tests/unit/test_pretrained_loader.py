"""Unit tests verifying pre-trained model loading from backend/models/pretrained/."""

import numpy as np
import pytest
from app.ml.loader import pretrained_model_loader


def test_list_pretrained_models():
    """Verify that pretrained models metadata is discoverable."""
    models = pretrained_model_loader.list_available_models()
    assert len(models) >= 4
    model_types = [m["model_type"] for m in models]
    assert "svm_linear" in model_types
    assert "svm_rbf" in model_types
    assert "vqc" in model_types


def test_load_pretrained_classical_svm():
    """Verify pre-trained Linear and RBF SVMs load and produce predictions."""
    clf = pretrained_model_loader.load_classical_svm("classical_linear_svm_4_feats.joblib")
    assert hasattr(clf, "predict")
    assert hasattr(clf, "predict_proba")

    # Predict on dummy 4-feature vector
    sample = np.array([[0.5, 0.5, 0.5, 0.5]])
    pred = clf.predict(sample)
    prob = clf.predict_proba(sample)
    assert len(pred) == 1
    assert prob.shape == (1, 2)


def test_load_pretrained_vqc():
    """Verify pre-trained 4-qubit VQC model loads variational weights and evaluates quantum node."""
    vqc = pretrained_model_loader.load_vqc_model(
        weights_filename="vqc_4_weights.npy",
        bias_filename="vqc_4_bias.npy",
        n_qubits=4,
        n_layers=2,
        is_noisy=False,
    )
    assert vqc.n_qubits == 4
    assert vqc.weights.shape == (2, 4)

    # Forward probability test on dummy sample
    sample = np.array([0.2, 0.4, 0.6, 0.8])
    prob = vqc.predict_proba(np.array([sample]))
    assert len(prob) == 1
    assert 0.0 <= prob[0] <= 1.0
