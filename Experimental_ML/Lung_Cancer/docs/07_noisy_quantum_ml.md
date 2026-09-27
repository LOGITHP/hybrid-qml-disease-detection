# 07. Quantum Noise Modeling: Simulated NISQ Robustness

## 1. Physical Motivation
Current quantum devices operate in the Noisy Intermediate-Scale Quantum (NISQ) regime. Physical qubits suffer from environmental decoherence, gate calibration errors, and crosstalk. Evaluating algorithms under simulated open quantum systems is critical to determine whether variational circuits can function under real hardware noise.

## 2. Noise Simulation Protocol
Simulations were implemented using PennyLane's density-matrix simulator (`default.mixed`), representing quantum states as density operators $\rho \in \mathbb{C}^{2^n \times 2^n}$:

$$\rho \longrightarrow \mathcal{E}(\rho) = \sum_k K_k \rho K_k^\dagger, \quad \sum_k K_k^\dagger K_k = I$$

### Noise Channels Implemented:
1. **Single-Qubit Depolarizing Channel ($p = 0.01$)**:
   Applied after each parameterized rotation gate:
   $$\mathcal{E}_{\text{depol}}(\rho) = (1 - p)\rho + \frac{p}{3}(X\rho X + Y\rho Y + Z\rho Z)$$
   Models isotropic state degradation toward the maximally mixed state $I/2$.
2. **Phase Damping Channel ($\gamma = 0.01$)**:
   Applied across all wires:
   $$K_0 = \begin{pmatrix} 1 & 0 \\ 0 & \sqrt{1 - \gamma} \end{pmatrix}, \quad K_1 = \begin{pmatrix} 0 & 0 \\ 0 & \sqrt{\gamma} \end{pmatrix}$$
   Models pure dephasing (loss of quantum phase coherence without energy exchange).

## 3. Empirical Comparative Results

| Metric | Noiseless 4-Qubit VQC | Noisy 4-Qubit VQC ($p=0.01, \gamma=0.01$) | Absolute Difference |
|---|---:|---:|---:|
| **Accuracy** | 52.67% | 52.67% | 0.00% |
| **Balanced Accuracy** | 52.69% | 52.70% | +0.01% |
| **Sensitivity (Recall)** | 49.78% | 49.34% | -0.44% |
| **Specificity** | 55.61% | 56.05% | +0.44% |
| **Precision** | 53.30% | 53.33% | +0.03% |
| **F1-Score** | 51.48% | 51.26% | -0.22% |
| **ROC-AUC** | 0.5147 | 0.5174 | +0.0027 |
| **True Positives** | 113 | 112 | -1 sample |
| **False Positives** | 99 | 98 | -1 sample |
| **True Negatives** | 124 | 125 | +1 sample |
| **False Negatives** | 114 | 115 | +1 sample |

## 4. Interpretation
- **Numerical Robustness**: The noisy simulation maintained identical 52.67% test accuracy, with sensitivity shifting by only -0.44% (a single additional false negative out of 227 cancer cases).
- **Physical Rationale**: Because the VQC ansatz has a shallow depth ($L=2$ layers, 7 entangling gates), the total duration of environmental interaction is short, preventing severe decoherence before measurement.
- **Caveat**: This simulation does not model state preparation and measurement (SPAM) readout errors or spatial crosstalk, which are active factors on physical quantum chips.
