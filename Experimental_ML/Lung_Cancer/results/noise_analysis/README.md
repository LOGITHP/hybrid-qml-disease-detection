# Quantum Noise Simulation & Resilience Analysis

## 1. Objective
This analysis compares the performance of the 4-qubit Variational Quantum Classifier (VQC) in an ideal noiseless simulation against a simulated noisy NISQ environment. The goal is to measure how open-system noise channels (depolarizing errors and phase damping) affect classification metrics on identical held-out test data.

## 2. Experimental Setup
- **Quantum Circuit**: 4 Qubits, 2 Layers, Angle Embedding $\text{RY}(x_i \cdot \pi)$, Linear Entanglement CNOT ladder.
- **Features Used**: `WHEEZING`, `YELLOW_FINGERS`, `AGE`, `SHORTNESS_OF_BREATH` (4 features).
- **Noiseless Simulator**: PennyLane `default.qubit` (analytic statevector simulation).
- **Noisy Simulator**: PennyLane `default.mixed` (density matrix simulation).
- **Simulated Noise Channels**:
  - Single-qubit Depolarizing Channel ($p = 0.01$) applied after each rotation gate.
  - Single-qubit Phase Damping Channel ($\gamma = 0.01$) applied across all wires.

## 3. Comparative Metric Table

| Metric | Noiseless 4-Qubit VQC | Noisy 4-Qubit VQC | Absolute Difference ($\Delta$) | Relative Change (%) |
|---|---:|---:|---:|---:|
| **Accuracy** | 52.67% (0.5267) | 52.67% (0.5267) | 0.0000 | 0.00% |
| **Balanced Accuracy** | 52.69% (0.5269) | 52.70% (0.5270) | +0.0001 | +0.02% |
| **Sensitivity (Recall)** | 49.78% (0.4978) | 49.34% (0.4934) | -0.0044 | -0.88% |
| **Specificity** | 55.61% (0.5561) | 56.05% (0.5605) | +0.0044 | +0.79% |
| **Precision** | 53.30% (0.5330) | 53.33% (0.5333) | +0.0003 | +0.06% |
| **F1-Score** | 51.48% (0.5148) | 51.26% (0.5126) | -0.0022 | -0.43% |
| **ROC-AUC** | 0.5147 | 0.5174 | +0.0027 | +0.52% |
| **True Positives** | 113 | 112 | -1 sample | - |
| **False Positives** | 99 | 98 | -1 sample | - |
| **True Negatives** | 124 | 125 | +1 sample | - |
| **False Negatives** | 114 | 115 | +1 sample | - |

## 4. Simple Interpretation
- **Accuracy**: The noisy simulation maintained an overall accuracy of 52.67%, identical to the noiseless baseline.
- **Sensitivity**: Sensitivity changed from 49.78% in the noiseless model to 49.34% in the noisy simulation, a difference of -0.44%. In terms of raw counts, the model correctly identified 112 positive cases under noise compared to 113 in the noiseless case (1 additional false negative out of 227 positive samples).
- **Specificity**: The noisy simulation increased specificity from 55.61% to 56.05%, a difference of +0.44% (1 fewer false positive out of 223 negative samples).
- **ROC-AUC**: The noisy simulation changed ROC-AUC from 0.5147 to 0.5174, a difference of +0.0027.
- **Interpretation**: The simulated noise channels caused minor shifts in prediction probabilities around the 0.50 threshold, resulting in a net movement of only two sample classifications across the entire 450-sample holdout set.

## 5. Important Research Distinctions & Limitations
- **Simulated Nature**: This experiment is strictly a simulated noise benchmark conducted on classical computer memory via density matrices (`default.mixed`). It does **not** constitute proof of physical quantum hardware fault-tolerance or hardware advantage.
- **Noise Scope**: Real physical quantum processors experience coherent errors, thermal relaxation ($T_1$), dephasing ($T_2$), measurement readout fidelity errors, and spatial crosstalk that were not simulated here.

## 6. Conclusion
The simulated noise experiment demonstrates that the shallow 2-layer, 4-qubit VQC maintains steady numerical stability under modest 1% depolarizing and dephasing error rates, with test accuracy remaining at 52.67% and sensitivity shifting by less than 0.5%.
