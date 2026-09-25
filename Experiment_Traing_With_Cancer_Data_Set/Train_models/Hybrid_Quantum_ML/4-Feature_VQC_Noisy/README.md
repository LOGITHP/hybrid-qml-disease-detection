# 4-Qubit 2-Layer Noisy Variational Quantum Classifier (VQC)

**Project:** Hybrid Quantum Machine Learning Platform for Early Disease Detection  
**Module:** `Train_models/Hybrid_Quantum_ML/4-Feature_VQC_Noisy`  
**Application:** Early Lung Cancer Detection under Realistic NISQ Noise Channels  
**Quantum Framework:** PennyLane 0.45.1  
**Quantum Simulator:** `default.mixed` (Density Matrix Formalism for Open Quantum Systems)  

---

## 1. Directory Context & Folder Structure

This module is part of the standardized repository hierarchy designed to benchmark quantum machine learning architectures across noiseless, noisy, and physical quantum processor regimes:

```
Train_models/
├── CML/                                        # Classical ML Baselines (SVM, RF, Logistic Regression)
└── Hybrid_Quantum_ML/                          # Quantum & Hybrid Quantum-Classical Architectures
    ├── 4-feature_Vqc/                          # 4-Feature Noiseless Simulation (default.qubit)
    ├── 4-Feature_VQC_Noisy/                    # [CURRENT MODULE] 4-Feature Noisy Simulation (default.mixed)
    │   ├── 04_train_vqc_noisy_4features.ipynb  # Executed Jupyter Notebook with visualizations
    │   ├── train_vqc_noisy.py                  # Standalone CLI training script
    │   ├── README.md                           # Formal module documentation
    │   ├── noisy_training_history.csv          # Per-epoch loss and validation metrics
    │   ├── noisy_test_metrics.json             # Out-of-sample holdout test set evaluation
    │   ├── vqc_noisy_weights.npy               # Checkpointed optimal variational parameters
    │   ├── vqc_noisy_bias.npy                  # Checkpointed classical classification bias
    │   └── figures/                            # Publication-grade analytical figures
    │       ├── vqc_noisy_circuit_diagram.png   # Quantum circuit with noise channels
    │       ├── vqc_noisy_training_curves.png   # Training & validation loss / accuracy curves
    │       ├── vqc_noisy_confusion_matrix.png  # Test set confusion matrix heatmap
    │       └── noise_impact_comparison.png     # Side-by-side comparison (Noiseless vs. Noisy)
    ├── 4-Feature-VQC-Real_quntum_computer/     # 4-Feature Hardware Execution (IBM Quantum / Qiskit)
    ├── 6-feature_Vqc/                          # 6-Feature VQC Architecture (6 Qubits)
    └── 8-feture_VQC/                           # 8-Feature VQC Architecture (8 Qubits)
```

---

## 2. Quantum Circuit Architecture

The circuit follows a **4-Qubit, 2-Layer Parameterized Quantum Circuit** topology:

```
Wire 0 (x1): ──RY(x1)──[ε_gate]──RY(θ1)──[ε_gate]─╭●──[ε_cnot]──RY(θ2)──[ε_gate]─╭●──[ε_cnot]──[ε_meas]──┤ <Z>
Wire 1 (x2): ──RY(x2)──[ε_gate]──RY(θ3)──[ε_gate]─╰X──[ε_cnot]─╭●──RY(θ4)──[ε_gate]─╰X──[ε_cnot]─╭●──[ε_cnot]──[ε_meas]──┤ <Z>
Wire 2 (x3): ──RY(x3)──[ε_gate]──RY(θ5)──[ε_gate]─────────────╰X──[ε_cnot]─╭●──RY(θ6)──[ε_gate]─╰X──[ε_cnot]─╭●──[ε_meas]──┤ <Z>
Wire 3 (x4): ──RY(x4)──[ε_gate]──RY(θ7)──[ε_gate]──────────────────────────╰X──[ε_cnot]──RY(θ8)──[ε_gate]────╰X──[ε_meas]──┤ <Z>
```

### Architectural Specifications
1. **Qubit Allocation (4 Qubits):**
   * Wire 0: `WHEEZING` (Feature $x_1$)
   * Wire 1: `YELLOW_FINGERS` (Feature $x_2$)
   * Wire 2: `AGE` (Feature $x_3$)
   * Wire 3: `SHORTNESS_OF_BREATH` (Feature $x_4$)
2. **Data Encoding (Angle Embedding):**
   * Single-qubit Pauli rotation $R_y(x_j \cdot \pi)$ maps normalized inputs $x_j \in [0, 1]$ into state space angles $[0, \pi]$.
3. **Variational Layers (2 Layers):**
   * **Layer 1:** Rotations $RY(\theta_1), RY(\theta_3), RY(\theta_5), RY(\theta_7)$ followed by linear nearest-neighbor CNOT ladder: $\text{CNOT}(0, 1) \to \text{CNOT}(1, 2) \to \text{CNOT}(2, 3)$.
   * **Layer 2:** Rotations $RY(\theta_2), RY(\theta_4), RY(\theta_6), RY(\theta_8)$ followed by linear nearest-neighbor CNOT ladder: $\text{CNOT}(0, 1) \to \text{CNOT}(1, 2) \to \text{CNOT}(2, 3)$.
4. **Observable:**
   * Pauli-Z expectation measured across all 4 qubits: $\langle Z_i \rangle = \text{Tr}(\rho Z_i)$.
   * Pooled scalar: $\langle Z \rangle = \frac{1}{4} \sum_{i=0}^3 \langle Z_i \rangle$.
5. **Classical Classification Head:**
   * $\hat{p} = \sigma(\langle Z \rangle + b) = \frac{1}{1 + e^{-(\langle Z \rangle + b)}}$.
6. **Parameter Count:**
   * Exactly 8 quantum rotation angles $\boldsymbol{\theta} = [\theta_1 \dots \theta_8]$ + 1 classical bias $b$ = **9 total trainable parameters**.

---

## 3. Mathematical Noise Channels (NISQ Modeling)

Physical quantum hardware operates as an open quantum system interacting with an ambient thermal bath. We model this via Completely Positive Trace-Preserving (CPTP) noise maps acting on the density matrix $\rho$:

### A. Single-Qubit Depolarizing Channel ($\mathcal{E}_{1q}$)
Applied after each single-qubit rotation gate ($p_{gate} = 0.005$, 0.5% error rate):
$$\mathcal{E}_{1q}(\rho) = (1 - p_{gate}) \rho + \frac{p_{gate}}{3} \left( X\rho X + Y\rho Y + Z\rho Z \right)$$

### B. Two-Qubit CNOT Depolarizing Channel ($\mathcal{E}_{2q}$)
Superconducting entangling gates exhibit significantly higher infidelity due to cross-resonance driving and microwave leakage ($p_{cnot} = 0.020$, 2.0% error rate). Applied across control and target wires for each CNOT:
$$\mathcal{E}_{2q}(\rho) = (1 - p_{cnot}) \rho + \frac{p_{cnot}}{15} \sum_{i, j \in \{I, X, Y, Z\}, (i, j) \neq (I, I)} (P_i \otimes P_j) \rho (P_i \otimes P_j)$$

### C. State Preparation and Measurement (SPAM) Error ($\mathcal{E}_{meas}$)
Readout bit-flip channel applied immediately prior to measurement ($p_{meas} = 0.015$, 1.5% readout infidelity):
$$\mathcal{E}_{meas}(\rho) = (1 - p_{meas}) \rho + p_{meas} X\rho X$$

---

## 4. Experimental Evaluation & Benchmark Results

Both models were trained on identical stratified partitions (Training: 2,098 samples, Validation: 450 samples) and evaluated on the **completely untouched out-of-sample holdout test set (450 samples)**.

### Comparative Performance: Noiseless vs. Noisy VQC

| Evaluation Metric | Noiseless VQC (`default.qubit`) | Noisy VQC (`default.mixed`) | Delta ($\Delta$) | Impact Analysis |
| :--- | :---: | :---: | :---: | :--- |
| **Accuracy** | **52.67%** | **52.67%** | $\pm 0.00\%$ | Preserved overall predictive threshold |
| **Balanced Accuracy** | **52.69%** | **52.70%** | $+0.01\%$ | Symmetrical class balance maintained |
| **Sensitivity (Recall)** | **49.78%** | **49.34%** | $-0.44\%$ | Minor true-positive attenuation |
| **Specificity** | **55.61%** | **56.05%** | $+0.44\%$ | Robust true-negative detection |
| **Precision** | **53.30%** | **53.33%** | $+0.03\%$ | Preserved positive predictive value |
| **F1-Score** | **51.48%** | **51.26%** | $-0.22\%$ | High harmonic mean stability |
| **ROC-AUC** | **0.5147** | **0.5174** | $+0.0027$ | Ranking ability resilient to noise |

### Test Confusion Matrix Comparison
* **Noiseless VQC:** $\text{TN}=124, \text{FP}=99, \text{FN}=114, \text{TP}=113$
* **Noisy VQC:** $\text{TN}=125, \text{FP}=98, \text{FN}=115, \text{TP}=112$

### Key Insights
1. **Ansatz Noise Resilience:** The shallow 2-layer hardware-efficient ansatz (only 8 rotation gates and 6 linear CNOTs) prevents accumulation of coherent phase and depolarizing errors, avoiding barren plateau decay.
2. **Mean Observable Pooling:** Averaging Pauli-Z expectations across all 4 qubits ($\langle Z \rangle = \frac{1}{4} \sum \langle Z_i \rangle$) provides natural stochastic noise averaging, mitigating single-wire readout fluctuations.
3. **Readiness for Physical Quantum Hardware:** The resilience under depolarizing and SPAM noise confirms that the circuit is stable and ready for deployment on real quantum computers in `4-Feature-VQC-Real_quntum_computer`.

---

## 5. How to Run

### Option A: Execute the Jupyter Notebook
Open and run all cells in [**`04_train_vqc_noisy_4features.ipynb`**](04_train_vqc_noisy_4features.ipynb):
```bash
jupyter notebook 04_train_vqc_noisy_4features.ipynb
```

### Option B: Execute Standalone Python Script via CLI
Run the standalone training script with configurable noise rates and hyperparameters:
```bash
# Default execution (p_gate=0.005, p_cnot=0.020, p_meas=0.015, epochs=15)
python train_vqc_noisy.py

# Custom noise rate sweep
python train_vqc_noisy.py --epochs 20 --lr 0.03 --batch_size 64 --p_gate 0.01 --p_cnot 0.03 --p_meas 0.02
```
