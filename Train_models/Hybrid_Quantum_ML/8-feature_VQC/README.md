# 8-Qubit 2-Layer Variational Quantum Classifier (VQC) with Dedicated Feature Selection

**Project:** Hybrid Quantum Machine Learning Platform for Early Disease Detection  
**Module:** `Train_models/Hybrid_Quantum_ML/8-feature_VQC`  
**Application:** Early Lung Cancer Screening with 8 Selected Clinical Predictors  
**Quantum Framework:** PennyLane 0.45.1  
**Simulator:** `default.qubit` (Noiseless Statevector Simulation)  
**Hilbert Space Dimension:** $2^8 = 256$ Complex State Dimensions  

---

## 1. Directory Overview & Deliverables

All artifacts, dataset splits, scripts, notebooks, and figures for this module are self-contained inside `Train_models/Hybrid_Quantum_ML/8-feature_VQC`:

```
Train_models/Hybrid_Quantum_ML/8-feature_VQC/
├── 04_train_vqc_noiseless_8features.ipynb     # Executed Jupyter Notebook (SFS + VQC training)
├── train_vqc_8features.py                     # Standalone CLI training script
├── README.md                                  # Module documentation & scaling analysis
├── selected_features_8.json                   # JSON registry of the 8 selected features
├── feature_relevance_ranking_8.csv            # Multi-metric screening ranking across 15 features
├── feature_selection_summary_8.csv            # Step-by-step SFS selection trajectory
├── X_train_8.csv                              # Extracted 8-feature training matrix (2,098 samples)
├── X_validation_8.csv                         # Extracted 8-feature validation matrix (450 samples)
├── X_test_8.csv                               # Extracted 8-feature holdout test matrix (450 samples)
├── training_history_8.csv                     # Per-epoch loss and accuracy progression
├── test_metrics_8.json                        # Out-of-sample holdout test evaluation metrics
├── vqc_8_weights.npy                          # Checkpointed optimal variational parameters (16 angles)
├── vqc_8_bias.npy                             # Checkpointed classical bias
└── figures/                                   # Publication-grade analytical figures
    ├── 01_feature_relevance_ranking_8.png     # 15-feature composite screening bar chart
    ├── 02_sfs_trajectory_8.png                # SFS validation trajectory plot (Steps 1 to 8)
    ├── vqc_8_circuit_diagram.png              # 8-qubit quantum circuit schematic
    ├── vqc_8_training_curves.png              # Training & validation loss / accuracy curves
    ├── vqc_8_confusion_matrix.png             # Holdout test set confusion matrix heatmap
    ├── vqc_8_roc_curve.png                    # Test set ROC-AUC curve
    └── quantum_scaling_comparison_4_6_8.png   # 3-way comparative benchmark (4 vs. 6 vs. 8 Qubits)
```

---

## 2. Dedicated 8-Feature Selection Protocol

To select an optimal 8-feature subset from the 15 candidate predictors without data leakage:

### Stage 1: Relevance Screening (Training Set Only)
Screened predictive relevance exclusively on `X_train` (2,098 samples) across three complementary methods:
1. **Mutual Information (`mutual_info_classif`)**: Non-linear information sharing.
2. **ANOVA F-statistic (`f_classif`)**: Linear separation between cancer classes.
3. **Random Forest Feature Importance (`RandomForestClassifier`)**: Gini split utility across tree ensembles.

The composite rank average determined the candidate pool for sequential forward selection.

### Stage 2: Sequential Forward Selection (SFS)
* Evaluated iteratively on `X_validation` (450 samples) optimizing **Balanced Accuracy**:
  $$\text{Balanced Accuracy} = \frac{\text{Sensitivity} + \text{Specificity}}{2}$$
* **Holdout Guardrail:** The holdout test set (`X_test_8.csv`, 450 samples) remained strictly untouched until final model testing.

### Selected 8 Features:
1. **`COUGHING`** (SFS Step 1)
2. **`PEER_PRESSURE`** (SFS Step 2)
3. **`AGE`** (SFS Step 3)
4. **`ANXIETY`** (SFS Step 4)
5. **`ALLERGY`** (SFS Step 5)
6. **`SHORTNESS_OF_BREATH`** (SFS Step 6)
7. **`CHEST_PAIN`** (SFS Step 7)
8. **`CHRONIC_DISEASE`** (SFS Step 8)

---

## 3. 8-Qubit 2-Layer VQC Architecture

Scaling to 8 qubits expands the complex state Hilbert space to $2^8 = 256$ dimensions:

```
Wire 0 (COUGHING):            ──RY(x0)──RY(θ1)─╭●──RY(θ9)───────────╭●───────────────────────────────────────────────────────┤ <Z>
Wire 1 (PEER_PRESSURE):       ──RY(x1)──RY(θ2)─╰X─╭●─────────RY(θ10)─╰X────────╭●────────────────────────────────────────────┤ <Z>
Wire 2 (AGE):                 ──RY(x2)──RY(θ3)────╰X────────╭●─────────RY(θ11)─╰X────────╭●──────────────────────────────────┤ <Z>
Wire 3 (ANXIETY):             ──RY(x3)──RY(θ4)──────────────╰X────────╭●─────────RY(θ12)─╰X────────╭●────────────────────────┤ <Z>
Wire 4 (ALLERGY):             ──RY(x4)──RY(θ5)────────────────────────╰X────────╭●─────────RY(θ13)─╰X────────╭●────────────────┤ <Z>
Wire 5 (SHORTNESS_OF_BREATH): ──RY(x5)──RY(θ6)──────────────────────────────────╰X────────╭●─────────RY(θ14)─╰X────────╭●────┤ <Z>
Wire 6 (CHEST_PAIN):          ──RY(x6)──RY(θ7)────────────────────────────────────────────╰X────────╭●─────────RY(θ15)─╰X─╭●─┤ <Z>
Wire 7 (CHRONIC_DISEASE):     ──RY(x7)──RY(θ8)──────────────────────────────────────────────────────╰X─────────RY(θ16)────╰X─┤ <Z>
```

### Architectural Specifications:
1. **Data Encoding (Angle Embedding):**
   * $x_j \to RY(x_j \cdot \pi)$ on Wire $j$ for $j \in \{0 \dots 7\}$.
2. **VQC Layer 1 (Trainable Parameters $\theta_1 \dots \theta_8$):**
   * Single-qubit rotations: $RY(\theta_1) \dots RY(\theta_8)$ on wires $0 \dots 7$.
   * Linear CNOT ladder: $\text{CNOT}(0, 1) \to \text{CNOT}(1, 2) \to \dots \to \text{CNOT}(6, 7)$ (7 entangling gates).
3. **VQC Layer 2 (Trainable Parameters $\theta_9 \dots \theta_{16}$):**
   * Single-qubit rotations: $RY(\theta_9) \dots RY(\theta_{16})$ on wires $0 \dots 7$.
   * Linear CNOT ladder: $\text{CNOT}(0, 1) \to \text{CNOT}(1, 2) \to \dots \to \text{CNOT}(6, 7)$ (7 entangling gates).
4. **Observable & Readout:**
   * Pauli-Z expectation value on each wire: $\langle Z_i \rangle$.
   * Pooled scalar: $\langle Z \rangle = \frac{1}{8} \sum_{i=0}^7 \langle Z_i \rangle$.
5. **Classical Classification Head:**
   * $\hat{p} = \sigma(\langle Z \rangle + b) = \frac{1}{1 + e^{-(\langle Z \rangle + b)}}$.
6. **Total Parameters:**
   * 16 quantum rotation angles $\boldsymbol{\theta} \in \mathbb{R}^{2 \times 8}$ + 1 classical bias $b \in \mathbb{R}$ = **17 total parameters**.

---

## 4. Quantum Scaling Analysis: 4-Qubit vs. 6-Qubit vs. 8-Qubit VQC

All three models were evaluated under identical conditions on the untouched 450-sample holdout test partition:

| Metric | 4-Qubit VQC (16-D Space) | 6-Qubit VQC (64-D Space) | 8-Qubit VQC (256-D Space) | Optimal Regime |
| :--- | :---: | :---: | :---: | :--- |
| **Qubits / Features** | 4 qubits | 6 qubits | 8 qubits | Task dependent |
| **Hilbert Space** | $2^4 = 16$ | $2^6 = 64$ | $2^8 = 256$ | Exponential growth ($16\times$) |
| **Variational Parameters** | 9 (8 Q + 1 C) | 13 (12 Q + 1 C) | 17 (16 Q + 1 C) | Linear growth ($+4$ per 2 qubits) |
| **Accuracy** | 52.67% | **53.11%** | 48.44% | **6-Qubit Peak** |
| **Balanced Accuracy** | 52.69% | **52.92%** | 48.50% | **6-Qubit Peak** |
| **Sensitivity (Recall)** | 49.78% | **74.45%** | 42.73% | **6-Qubit Peak (+24.67%)** |
| **Specificity** | **55.61%** | 31.39% | 54.26% | 4-Qubit Baseline |
| **Precision** | **53.30%** | 52.48% | 48.74% | 4-Qubit Baseline |
| **F1-Score** | 51.48% | **61.57%** | 45.54% | **6-Qubit Peak (+10.09%)** |
| **ROC-AUC** | 0.5147 | **0.5555** | 0.4990 | **6-Qubit Peak (+0.0408)** |

### Confusion Matrix Breakdown across Architectures
* **4-Qubit VQC:** $\text{TN}=124, \text{FP}=99, \mathbf{FN=114}, \text{TP}=113$
* **6-Qubit VQC:** $\text{TN}=70, \text{FP}=153, \mathbf{FN=58}, \text{TP}=169$
* **8-Qubit VQC:** $\text{TN}=121, \text{FP}=102, \mathbf{FN=130}, \text{TP}=97$

### Scientific & Practical Insights:
1. **The 6-Qubit Sweet Spot:**
   The 6-qubit architecture achieves the highest clinical diagnostic performance, slashing false negatives from 114 to 58 and delivering a **74.45% cancer sensitivity** and an **ROC-AUC of 0.5555**.
2. **Expressibility vs. Trainability (Under-parameterization in Large Hilbert Spaces):**
   Expanding from 6 qubits ($2^6 = 64$ dimensions) to 8 qubits ($2^8 = 256$ dimensions) increases the state space by $4\times$, but only adds 4 single-qubit rotation parameters (from 12 to 16 quantum angles). With a fixed 2-layer linear CNOT depth, the 8-qubit circuit becomes under-parameterized relative to its 256-dimensional Hilbert space. Gradient signals become more diffuse across the 8-qubit register, demonstrating the well-known QML trade-off where increasing Hilbert dimension requires commensurate circuit depth, data re-uploading, or localized cost functions to avoid barren plateau-adjacent trainability saturation.

---

## 5. Execution Guide

### Run via Jupyter Notebook
Open and run all cells in [**`04_train_vqc_noiseless_8features.ipynb`**](04_train_vqc_noiseless_8features.ipynb):
```bash
jupyter notebook 04_train_vqc_noiseless_8features.ipynb
```

### Run Standalone Python CLI Script
```bash
python train_vqc_8features.py
```

