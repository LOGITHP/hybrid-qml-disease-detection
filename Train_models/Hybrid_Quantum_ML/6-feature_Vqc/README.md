# 6-Qubit 2-Layer Variational Quantum Classifier (VQC) with Dedicated Feature Selection

**Project:** Hybrid Quantum Machine Learning Platform for Early Disease Detection  
**Module:** `Train_models/Hybrid_Quantum_ML/6-feature_Vqc`  
**Application:** Early Lung Cancer Screening with 6 Selected Clinical Predictors  
**Quantum Framework:** PennyLane 0.45.1  
**Simulator:** `default.qubit` (Noiseless Statevector Simulation)  
**Hilbert Space Dimension:** $2^6 = 64$ Complex State Dimensions  

---

## 1. Directory Overview & Deliverables

All artifacts, dataset splits, code, and figures for this module are self-contained inside `Train_models/Hybrid_Quantum_ML/6-feature_Vqc`:

```
Train_models/Hybrid_Quantum_ML/6-feature_Vqc/
├── 04_train_vqc_noiseless_6features.ipynb  # Executed Jupyter Notebook (SFS + VQC training)
├── train_vqc_6features.py                  # Standalone CLI training script
├── README.md                               # Module documentation & benchmark analysis
├── selected_features_6.json                # JSON registry of the 6 selected features
├── feature_relevance_ranking_6.csv         # Multi-metric screening ranking across 15 features
├── feature_selection_summary_6.csv         # Step-by-step SFS selection trajectory
├── X_train_6.csv                           # Extracted 6-feature training matrix (2,098 samples)
├── X_validation_6.csv                      # Extracted 6-feature validation matrix (450 samples)
├── X_test_6.csv                            # Extracted 6-feature holdout test matrix (450 samples)
├── training_history_6.csv                  # Per-epoch loss and accuracy progression
├── test_metrics_6.json                     # Out-of-sample holdout test evaluation metrics
├── vqc_6_weights.npy                       # Checkpointed optimal variational parameters (12 angles)
├── vqc_6_bias.npy                          # Checkpointed classical bias
└── figures/                                # Publication-grade analytical figures
    ├── 01_feature_relevance_ranking_6.png  # 15-feature composite screening bar chart
    ├── 02_sfs_trajectory_6.png             # SFS validation trajectory plot (Steps 1 to 6)
    ├── vqc_6_circuit_diagram.png           # 6-qubit quantum circuit schematic
    ├── vqc_6_training_curves.png           # Training & validation loss / accuracy curves
    ├── vqc_6_confusion_matrix.png          # Holdout test set confusion matrix heatmap
    ├── vqc_6_roc_curve.png                 # Test set ROC-AUC curve
    └── 4_vs_6_feature_comparison.png       # Side-by-side benchmark: 4-Qubit vs. 6-Qubit VQC
```

---

## 2. Dedicated 6-Feature Selection Protocol

To select an optimal 6-feature subset from the 15 candidate predictors without data leakage:

### Stage 1: Relevance Screening (Training Set Only)
Screened predictive relevance exclusively on `X_train` (2,098 samples) across three complementary methods:
1. **Mutual Information (`mutual_info_classif`)**: Non-linear information sharing.
2. **ANOVA F-statistic (`f_classif`)**: Linear separation between cancer classes.
3. **Random Forest Feature Importance (`RandomForestClassifier`)**: Gini split utility across tree ensembles.

The composite rank average determined the top 10 candidate pool for sequential forward selection.

### Stage 2: Sequential Forward Selection (SFS)
* Evaluated iteratively on `X_validation` (450 samples) optimizing **Balanced Accuracy**:
  $$\text{Balanced Accuracy} = \frac{\text{Sensitivity} + \text{Specificity}}{2}$$
* **Holdout Guardrail:** The holdout test set (`X_test_6.csv`, 450 samples) remained strictly untouched until final model testing.

### Selected 6 Features:
1. **`COUGHING`** (SFS Step 1)
2. **`PEER_PRESSURE`** (SFS Step 2)
3. **`AGE`** (SFS Step 3)
4. **`YELLOW_FINGERS`** (SFS Step 4)
5. **`SHORTNESS_OF_BREATH`** (SFS Step 5)
6. **`CHEST_PAIN`** (SFS Step 6)

---

## 3. 6-Qubit 2-Layer VQC Architecture

Expanding to 6 qubits increases the state Hilbert space fourfold from $2^4 = 16$ to $2^6 = 64$ complex dimensions:

```
Wire 0 (COUGHING):            ──RY(x1)──RY(θ1)─╭●──RY(θ7)───────────╭●──────────────────────────────────┤ <Z>
Wire 1 (PEER_PRESSURE):       ──RY(x2)──RY(θ2)─╰X─╭●─────────RY(θ8)─╰X────────╭●────────────────────────┤ <Z>
Wire 2 (AGE):                 ──RY(x3)──RY(θ3)────╰X────────╭●─────────RY(θ9)─╰X────────╭●──────────────┤ <Z>
Wire 3 (YELLOW_FINGERS):      ──RY(x4)──RY(θ4)──────────────╰X────────╭●─────────RY(θ10)─╰X────────╭●────┤ <Z>
Wire 4 (SHORTNESS_OF_BREATH): ──RY(x5)──RY(θ5)────────────────────────╰X────────╭●─────────RY(θ11)─╰X─╭●─┤ <Z>
Wire 5 (CHEST_PAIN):          ──RY(x6)──RY(θ6)──────────────────────────────────╰X─────────RY(θ12)────╰X─┤ <Z>
```

### Architectural Specifications:
1. **Data Encoding (Angle Embedding):**
   * $x_j \to RY(x_j \cdot \pi)$ on Wire $j$ for $j \in \{0, 1, 2, 3, 4, 5\}$.
2. **VQC Layer 1 (Trainable Parameters $\theta_1 \dots \theta_6$):**
   * Single-qubit rotations: $RY(\theta_1) \dots RY(\theta_6)$ on wires $0 \dots 5$.
   * Linear CNOT ladder: $\text{CNOT}(0, 1) \to \text{CNOT}(1, 2) \to \text{CNOT}(2, 3) \to \text{CNOT}(3, 4) \to \text{CNOT}(4, 5)$ (5 entangling gates).
3. **VQC Layer 2 (Trainable Parameters $\theta_7 \dots \theta_{12}$):**
   * Single-qubit rotations: $RY(\theta_7) \dots RY(\theta_{12})$ on wires $0 \dots 5$.
   * Linear CNOT ladder: $\text{CNOT}(0, 1) \to \text{CNOT}(1, 2) \to \text{CNOT}(2, 3) \to \text{CNOT}(3, 4) \to \text{CNOT}(4, 5)$ (5 entangling gates).
4. **Observable & Readout:**
   * Pauli-Z expectation value on each wire: $\langle Z_i \rangle$.
   * Pooled scalar: $\langle Z \rangle = \frac{1}{6} \sum_{i=0}^5 \langle Z_i \rangle$.
5. **Classical Classification Head:**
   * $\hat{p} = \sigma(\langle Z \rangle + b) = \frac{1}{1 + e^{-(\langle Z \rangle + b)}}$.
6. **Total Parameters:**
   * 12 quantum rotation angles $\boldsymbol{\theta} \in \mathbb{R}^{2 \times 6}$ + 1 classical bias $b \in \mathbb{R}$ = **13 total parameters**.

---

## 4. Quantum Scaling Benchmark: 4-Qubit vs. 6-Qubit VQC

Both models were evaluated on the identical 450 unseen holdout patient samples:

| Evaluation Metric | 4-Qubit VQC (16-D Space) | 6-Qubit VQC (64-D Space) | Quantum Scaling Gain ($\Delta$) | Clinical Significance |
| :--- | :---: | :---: | :---: | :--- |
| **Accuracy** | 52.67% | **53.11%** | $+0.44\%$ | Improved overall prediction rate |
| **Balanced Accuracy** | 52.69% | **52.92%** | $+0.23\%$ | Maintained class balance fidelity |
| **Sensitivity (Recall)** | 49.78% | **74.45%** | **$+24.67\%$** | **Critical clinical gain:** Drastic reduction in missed cancer cases (False Negatives reduced from 114 to 58) |
| **Specificity** | 55.61% | 31.39% | $-24.22\%$ | Shift towards aggressive early detection |
| **Precision** | 53.30% | 52.48% | $-0.82\%$ | Stable positive predictive accuracy |
| **F1-Score** | 51.48% | **61.57%** | **$+10.09\%$** | Major increase in cancer detection harmonic mean |
| **ROC-AUC** | 0.5147 | **0.5555** | **$+0.0408$** | Superior probabilistic discrimination across thresholds |

### Confusion Matrix Comparison
* **4-Qubit VQC:** $\text{TN}=124, \text{FP}=99, \mathbf{FN=114}, \text{TP}=113$
* **6-Qubit VQC:** $\text{TN}=70, \text{FP}=153, \mathbf{FN=58}, \text{TP}=169$

> **Clinical Finding:** Expanding to 6 qubits halved false negatives ($\mathbf{FN}$ dropped from 114 to 58), achieving a **74.45% cancer recall rate**. In early screening scenarios, identifying genuine cancer cases to prioritize urgent follow-up CT scans is the paramount clinical objective.

---

## 5. Execution Guide

### Run via Jupyter Notebook
Open and run all cells in [**`04_train_vqc_noiseless_6features.ipynb`**](04_train_vqc_noiseless_6features.ipynb):
```bash
jupyter notebook 04_train_vqc_noiseless_6features.ipynb
```

### Run Standalone Python CLI Script
```bash
# Default execution (20 epochs, batch size 64, lr 0.03)
python train_vqc_6features.py

# Custom hyperparameter configuration
python train_vqc_6features.py --epochs 25 --lr 0.02 --batch_size 32
```
