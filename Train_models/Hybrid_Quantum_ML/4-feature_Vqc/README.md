# 4-Qubit 2-Layer Variational Quantum Classifier (VQC) Baseline

**Project:** Hybrid Quantum Machine Learning Platform for Early Disease Detection  
**Module:** `Train_models/Hybrid_Quantum_ML/4-feature_Vqc`  
**Application:** Early Lung Cancer Screening with 4 Clinical Features  
**Quantum Framework:** PennyLane 0.45.1  
**Simulator:** `default.qubit` (Noiseless Statevector Simulation)  
**Hilbert Space Dimension:** $2^4 = 16$ Complex State Dimensions  

---

## 1. Directory Overview & Deliverables

```
Train_models/Hybrid_Quantum_ML/4-feature_Vqc/
├── 04_train_vqc_noiseless_4features.ipynb  # Executed Jupyter Notebook
├── train_vqc.py                            # Standalone CLI training script
├── README.md                               # Module documentation & analysis
├── test_metrics.json                       # Out-of-sample holdout test metrics
├── training_history.csv                    # Epoch-by-epoch loss & accuracy history
├── vqc_weights.npy                         # Checkpointed optimal variational parameters (8 angles)
├── vqc_bias.npy                            # Checkpointed classical bias
└── figures/                                # High-resolution figures
    ├── vqc_circuit_diagram.png             # 4-qubit quantum circuit schematic
    ├── vqc_training_curves.png             # BCE loss and validation accuracy progression
    ├── vqc_confusion_matrix.png            # Holdout test set confusion matrix heatmap
    └── vqc_roc_curve.png                   # Test set ROC-AUC curve
```

---

## 2. Selected Features & Clinical Rationale

The baseline 4 features selected through training-derived relevance and sequential selection:
1. **`WHEEZING`**: High-pitched continuous breathing sound indicating respiratory tract obstruction.
2. **`YELLOW_FINGERS`**: Physical biomarker of chronic tobacco exposure and heavy smoking.
3. **`AGE`**: Continuous demographic baseline strongly correlated with cumulative oncological mutation risk.
4. **`SHORTNESS_OF_BREATH`**: Dyspnea and impaired gas exchange indicating compromised pulmonary function.

---

## 3. Quantum Circuit Architecture

* **Qubits:** 4 Wires ($q_0, q_1, q_2, q_3$)
* **Encoding (Angle Embedding):** $x_j \to RY(x_j \cdot \pi)$ on Wire $j$.
* **Layer 1:** 4 parameterized $RY(\theta_1 \dots \theta_4)$ rotations + Linear CNOT ladder ($0\to 1\to 2\to 3$).
* **Layer 2:** 4 parameterized $RY(\theta_5 \dots \theta_8)$ rotations + Linear CNOT ladder ($0\to 1\to 2\to 3$).
* **Measurement:** Mean Pauli-Z expectation value: $\langle Z \rangle = \frac{1}{4}\sum_{i=0}^3 \langle Z_i \rangle$.
* **Classification Head:** $\hat{p} = \sigma(\langle Z \rangle + b)$.
* **Total Parameters:** 8 quantum rotation angles + 1 classical bias = **9 parameters**.

---

## 4. Test Set Evaluation Results (450 Held-Out Patients)

* **Accuracy:** 52.67%
* **Balanced Accuracy:** 52.69%
* **Sensitivity (Recall):** 49.78%
* **Specificity:** 55.61%
* **Precision:** 53.30%
* **F1-Score:** 51.48%
* **ROC-AUC:** 0.5147
* **Confusion Matrix:**
  * True Negative (TN): 124
  * False Positive (FP): 99
  * False Negative (FN): 114
  * True Positive (TP): 113

---

## 5. Execution Guide

### Run via Jupyter Notebook
Open and run all cells in [**`04_train_vqc_noiseless_4features.ipynb`**](04_train_vqc_noiseless_4features.ipynb):
```bash
jupyter notebook 04_train_vqc_noiseless_4features.ipynb
```

### Run Standalone Python CLI Script
```bash
python train_vqc.py
```
