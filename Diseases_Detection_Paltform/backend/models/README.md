# Pre-trained Models in Backend

This directory contains pre-trained classical and quantum machine learning models imported directly from the repository's research experiments:

## 1. Classical Machine Learning Models (`backend/models/pretrained/`)

- **`classical_linear_svm_4_feats.joblib`**: Linear Support Vector Classifier trained on the 4 canonical screening features:
  - `WHEEZING`
  - `YELLOW_FINGERS`
  - `AGE`
  - `SHORTNESS_OF_BREATH`
- **`classical_rbf_svm_4_feats.joblib`**: Radial Basis Function (RBF) Support Vector Classifier trained on the same 4 features with probability estimation enabled.

## 2. Quantum Machine Learning Models (`backend/models/pretrained/`)

- **4-Qubit Noiseless VQC (`vqc_4_weights.npy`, `vqc_4_bias.npy`):**
  - Architecture: 4 qubits, 2 variational layers ($2 \times 4 = 8$ variational parameters $\theta + 1$ bias).
  - Encoding: AngleEmbedding via $\text{RY}(x_i \cdot \pi)$ on wire $i$.
  - Entanglement: Linear CNOT chain ($0 \to 1 \to 2 \to 3$).
  - Measurement: Pauli-Z expectation value across all 4 qubits.
- **4-Qubit Noisy NISQ VQC (`vqc_noisy_4_weights.npy`, `vqc_noisy_4_bias.npy`):**
  - Evaluated on PennyLane `default.mixed` open quantum system simulator with depolarizing noise ($p_{\text{gate}} = 1\%$, $p_{\text{cnot}} = 2\%$) and readout bit-flip error ($p_{\text{meas}} = 1\%$).
- **6-Qubit Noiseless VQC (`vqc_6_weights.npy`, `vqc_6_bias.npy`):**
  - Architecture: 6 qubits, 2 variational layers ($2 \times 6 = 12$ variational parameters $\theta + 1$ bias).
- **8-Qubit Noiseless VQC (`vqc_8_weights.npy`, `vqc_8_bias.npy`):**
  - Architecture: 8 qubits, 2 variational layers ($2 \times 8 = 16$ variational parameters $\theta + 1$ bias).

## 3. Metadata and Loading

All models are cataloged with hyperparameters, feature lists, and provenance in [`metadata.json`](file:///backend/models/pretrained/metadata.json) and can be loaded dynamically using the loader utility in [`app/ml/loader.py`](file:///backend/app/ml/loader.py):

```python
from app.ml.loader import pretrained_model_loader

# Load Classical Linear SVM
svm = pretrained_model_loader.load_classical_svm("classical_linear_svm_4_feats.joblib")

# Load 4-Qubit VQC
vqc = pretrained_model_loader.load_vqc_model(
    weights_filename="vqc_4_weights.npy",
    bias_filename="vqc_4_bias.npy",
    n_qubits=4,
    n_layers=2,
)
```
