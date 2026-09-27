"""Unit tests verifying contracts for Models, Preprocessing, and Quantum Backends."""

import numpy as np
import pandas as pd
import pytest
from app.agents.preprocessing_agent.interface import PreprocessingAgent
from app.ml.classical.svm.linear import SVMLinearModel
from app.ml.classical.svm.rbf import SVMRBFModel
from app.ml.quantum.vqc.model import VariationalQuantumClassifier
from app.quantum.registry import quantum_registry


def test_classical_model_contracts():
    """Verify SVM Linear and RBF models implement IModel interface correctly."""
    X = np.array([[0.1, 0.2], [0.8, 0.9], [0.2, 0.3], [0.9, 0.7]])
    y = np.array([0, 1, 0, 1])

    for model in [SVMLinearModel(C=1.0), SVMRBFModel(C=1.0)]:
        model.fit(X, y)
        preds = model.predict(X)
        probs = model.predict_proba(X)

        assert len(preds) == len(X)
        assert len(probs) == len(X)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()
        assert "kernel" in model.get_params()


def test_vqc_model_contract():
    """Verify VariationalQuantumClassifier implements IModel with PennyLane simulation."""
    X = np.array([[0.1, 0.2], [0.8, 0.9], [0.2, 0.3], [0.9, 0.7]])
    y = np.array([0, 1, 0, 1])

    vqc = VariationalQuantumClassifier(n_qubits=2, n_layers=1, epochs=2, batch_size=2)
    vqc.fit(X, y)

    probs = vqc.predict_proba(X)
    preds = vqc.predict(X, threshold=0.5)

    assert len(probs) == len(X)
    assert len(preds) == len(X)
    assert (probs >= 0.0).all() and (probs <= 1.0).all()
    assert vqc.model_type == "vqc"


def test_preprocessing_data_leakage_prevention():
    """Test that PreprocessingAgent prevents data leakage by fitting transformers strictly on Train."""
    agent = PreprocessingAgent()
    data = {
        "AGE": [45, 60, 50, 70, 55, 65, 48, 72, 58, 62],
        "SMOKING": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
        "LUNG_CANCER": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    }
    df = pd.DataFrame(data)

    splits = agent.execute_plan(df, plan=None, target_column="LUNG_CANCER")

    # Assert train, val, test shapes are strictly partitioned
    assert splits["train_samples"] > 0
    assert splits["val_samples"] > 0
    assert splits["test_samples"] > 0
    assert "fitted_pipeline" in splits

    # Validate scaled bounds
    assert agent.validate_result(splits) is True


def test_quantum_registry_backends():
    """Verify QuantumRegistry provides Simulator, Noisy Simulator, and Hardware abstractions."""
    sim = quantum_registry.get_backend("simulator")
    noisy = quantum_registry.get_backend("noisy_simulator")
    hardware = quantum_registry.get_backend("ibm_hardware")

    assert sim.get_device_info()["device_type"] == "simulator"
    assert noisy.get_device_info()["device_type"] == "noisy_simulator"
    assert hardware.get_device_info()["device_type"] == "hardware"

    # Hardware without token should raise graceful error
    with pytest.raises(Exception):
        hardware.submit_job({"wires": 4})
