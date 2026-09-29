"""Variational Quantum Classifier (VQC) wrapper implementing IModel interface."""

from typing import Any, Dict, Optional
import numpy as np
from pennylane import numpy as pnp
import pennylane as qml
from app.interfaces.model import IModel
from app.ml.quantum.vqc.circuit import create_vqc_circuit
from app.ml.quantum.vqc.noisy import create_noisy_vqc_circuit


class VariationalQuantumClassifier(IModel):
    """Production wrapper around the validated repository VQC implementation."""

    def __init__(
        self,
        n_qubits: int = 4,
        n_layers: int = 2,
        lr: float = 0.03,
        epochs: int = 10,
        batch_size: int = 32,
        is_noisy: bool = False,
        noise_params: Optional[Dict[str, float]] = None,
        random_seed: int = 42,
    ):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.is_noisy = is_noisy
        self.noise_params = noise_params or {"p_gate": 0.01, "p_cnot": 0.02, "p_meas": 0.01}
        self.random_seed = random_seed

        # Initialize trainable variational parameters
        np.random.seed(self.random_seed)
        pnp.random.seed(self.random_seed)
        self.weights = pnp.random.uniform(0.0, 2.0 * pnp.pi, (self.n_layers, self.n_qubits), requires_grad=True)
        self.bias = pnp.array(0.0, requires_grad=True)

        # Build quantum circuit
        if self.is_noisy:
            self.circuit = create_noisy_vqc_circuit(
                n_qubits=self.n_qubits,
                n_layers=self.n_layers,
                **self.noise_params,
            )
        else:
            self.circuit = create_vqc_circuit(
                n_qubits=self.n_qubits,
                n_layers=self.n_layers,
            )

    @property
    def model_type(self) -> str:
        return "vqc"

    def _forward_single(self, x: np.ndarray, weights, bias) -> float:
        """Compute probability for a single sample."""
        res = self.circuit(x, weights)
        z_mean = pnp.mean(pnp.stack(res))
        logit = z_mean + bias
        return float(1.0 / (1.0 + pnp.exp(-logit)))

    def _forward_batch(self, X: np.ndarray, weights, bias) -> np.ndarray:
        """Compute probabilities for a batch of feature vectors."""
        probs = []
        for i in range(len(X)):
            res = self.circuit(X[i], weights)
            z_mean = pnp.mean(pnp.stack(res))
            logit = z_mean + bias
            p = 1.0 / (1.0 + pnp.exp(-logit))
            probs.append(p)
        return pnp.array(probs)

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs: Any) -> "VariationalQuantumClassifier":
        """Train variational parameters using gradient descent / Adam optimizer."""
        # Scale/bound features to [0, 1] if not already bounded
        X_pnp = pnp.array(X, requires_grad=False)
        y_pnp = pnp.array(y, requires_grad=False)
        num_samples = len(X)

        opt = qml.AdamOptimizer(stepsize=self.lr)

        def cost(weights, bias, batch_x, batch_y):
            probs = self._forward_batch(batch_x, weights, bias)
            probs_clipped = pnp.clip(probs, 1e-7, 1.0 - 1e-7)
            return -pnp.mean(batch_y * pnp.log(probs_clipped) + (1.0 - batch_y) * pnp.log(1.0 - probs_clipped))

        for epoch in range(self.epochs):
            indices = np.random.permutation(num_samples)
            for start_idx in range(0, num_samples, self.batch_size):
                batch_idx = indices[start_idx : start_idx + self.batch_size]
                batch_x = X_pnp[batch_idx]
                batch_y = y_pnp[batch_idx]

                (self.weights, self.bias), _ = opt.step_and_cost(
                    lambda w, b: cost(w, b, batch_x, batch_y),
                    self.weights,
                    self.bias,
                )

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return array of probability scores for the positive disease class."""
        probs = []
        for i in range(len(X)):
            prob = self._forward_single(X[i], self.weights, self.bias)
            probs.append(prob)
        return np.array(probs)

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Generate binary labels using configurable threshold."""
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(int)

    def get_params(self) -> Dict[str, Any]:
        return {
            "n_qubits": self.n_qubits,
            "n_layers": self.n_layers,
            "lr": self.lr,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "is_noisy": self.is_noisy,
            "noise_params": self.noise_params,
            "weights": self.weights.tolist() if hasattr(self.weights, "tolist") else None,
            "bias": float(self.bias),
        }

    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove the unpicklable QNode
        if "circuit" in state:
            del state["circuit"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Recreate the quantum circuit
        if self.is_noisy:
            self.circuit = create_noisy_vqc_circuit(
                n_qubits=self.n_qubits,
                n_layers=self.n_layers,
                **self.noise_params,
            )
        else:
            self.circuit = create_vqc_circuit(
                n_qubits=self.n_qubits,
                n_layers=self.n_layers,
            )
