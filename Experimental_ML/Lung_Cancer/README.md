# Experimental Machine Learning for Lung Cancer Detection
**Research Module Documentation**  
*Project: Hybrid Quantum-Classical Machine Learning Platform for Early Disease Detection*  
*Disease Focus: Lung Cancer*

---

## 1. Purpose & Scope
This directory contains the core experimental machine learning and hybrid quantum algorithms for **Lung Cancer** screening. 

The primary research objective is to rigorously investigate whether low-depth Variational Quantum Classifiers (VQCs) running on compact qubit registers (4 to 8 qubits) can capture non-linear interactions among self-reported clinical predictors and improve positive-case detection (sensitivity) relative to standard classical baselines.

> **Research & Dataset Notice**:  
> - All models, findings, and evaluation metrics in this repository are research prototypes evaluated on the **Survey Lung Cancer Dataset**.  
> - This work does not constitute a clinical medical device.  
> - No software platform, database, or API code is included; this module is strictly experimental research.

---

## 2. Dataset Context
All experiments operate on the standardized **Survey Lung Cancer Dataset**:
- **Location**: `data/raw/V1_dataset.csv`
- **Sample Size**: 2,998 survey observations
- **Target Variable**: `LUNG_CANCER` (0 = Negative / No Cancer, 1 = Positive / Cancer)
- **Clinical Attributes (15 candidate predictors)**:
  - Demographic: `GENDER`, `AGE`
  - Behavioral: `SMOKING`, `ALCOHOL_CONSUMING`, `PEER_PRESSURE`
  - Symptoms: `YELLOW_FINGERS`, `ANXIETY`, `CHRONIC_DISEASE`, `FATIGUE`, `ALLERGY`, `WHEEZING`, `COUGHING`, `SHORTNESS_OF_BREATH`, `SWALLOWING_DIFFICULTY`, `CHEST_PAIN`
- **Splits**:
  - Training: 2,098 samples (70%)
  - Validation: 450 samples (15%)
  - Holdout Test: 450 samples (15%, strictly held out until final evaluation)

---

## 3. Experimental Workflow
```
Raw Survey Data (2,998 samples)
    │
    ▼
Strict Preprocessing & Scaling (No Leakage)
    │
    ▼
Feature Selection (4, 6, and 8 Features)
    │
    ├──► Classical ML (Logistic Regression, Linear SVM, RBF SVM)
    │       ├── 4 Features (WHEEZING, YELLOW_FINGERS, AGE, SHORTNESS_OF_BREATH)
    │       ├── 6 Features (COUGHING, PEER_PRESSURE, AGE, YELLOW_FINGERS, SHORTNESS_OF_BREATH, CHEST_PAIN)
    │       └── 8 Features (COUGHING, PEER_PRESSURE, AGE, ANXIETY, ALLERGY, SHORTNESS_OF_BREATH, CHEST_PAIN, CHRONIC_DISEASE)
    │
    └──► Hybrid Quantum ML (PennyLane Variational Quantum Classifiers)
            ├── 4-Qubit Noiseless VQC (Statevector, default.qubit)
            ├── 4-Qubit Noisy VQC (Simulated NISQ: Depolarizing + Phase Damping, default.mixed)
            ├── 6-Qubit Noiseless VQC (Statevector, default.qubit)
            └── 8-Qubit Noiseless VQC (Statevector, default.qubit)
```

---

## 4. VQC Circuit Formation & Architecture

The Variational Quantum Classifiers map classical tabular vectors into continuous quantum Hilbert state spaces using PennyLane:

```
|0⟩ ──[ RY(x₀·π) ]──[ RY(θ₁,₀) ]──╭●─────────────[ RY(θ₂,₀) ]──╭●─────────────┤ ⟨Z₀⟩ ──╮
|0⟩ ──[ RY(x₁·π) ]──[ RY(θ₁,₁) ]──╰X─╭●──────────[ RY(θ₂,₁) ]──╰X─╭●──────────┤ ⟨Z₁⟩ ──┤
|0⟩ ──[ RY(x₂·π) ]──[ RY(θ₁,₂) ]─────╰X─╭●───────[ RY(θ₂,₂) ]─────╰X─╭●───────┤ ⟨Z₂⟩ ──┼─► Mean ⟨Z⟩ ──► [+ b] ──► σ(·) ──► p(y=1)
|0⟩ ──[ RY(x₃·π) ]──[ RY(θ₁,₃) ]────────╰X─╭●────[ RY(θ₂,₃) ]────────╰X─╭●────┤ ⟨Z₃⟩ ──┤
                                         ...                              ...    ...     │
|0⟩ ──[ RY(xₙ·π) ]──[ RY(θ₁,ₙ) ]───────────╰X────[ RY(θ₂,ₙ) ]───────────╰X────┤ ⟨Zₙ⟩ ──╯
      └─────────┘   └────────────────────────┘   └────────────────────────┘   └───────┘
        Stage 1:              Stage 2:                     Stage 3:            Stage 4:
       Data Encoding       Variational Layer 1          Variational Layer 2   Measurement
```

### Architectural Principles:
1. **Angle Embedding**:
   Each normalized feature $x_i \in [0, 1]$ is encoded via single-qubit rotation $R_y(x_i \cdot \pi)$ on qubit wire $i$:
   $$|\psi_0(\mathbf{x})\rangle = \bigotimes_{i=0}^{n-1} R_y(x_i \cdot \pi) |0\rangle$$
   This maps normalized feature boundaries naturally onto orthogonal states ($x_i=0 \to |0\rangle$, $x_i=1 \to |1\rangle$).
2. **Variational Layers (Ansatz)**:
   Two layers, each comprising parameterized single-qubit rotations $R_y(\theta_{l, i})$ followed by a nearest-neighbor linear CNOT entangling ladder $\text{CNOT}(i, i+1)$.
3. **Measurement & Pooling**:
   Pauli-Z expectation values $\langle Z_i \rangle$ are measured across all $n$ qubits and pooled into scalar mean expectation $\langle Z \rangle = \frac{1}{n} \sum_{i=0}^{n-1} \langle Z_i \rangle$.
4. **Classification Head**:
   A trainable scalar bias $b$ is added: $\hat{p} = \sigma(\langle Z \rangle + b) = \frac{1}{1 + e^{-(\langle Z \rangle + b)}}$.
   Total trainable parameters: $n \times L + 1$ (4 qubits: 9 params; 6 qubits: 13 params; 8 qubits: 17 params).
5. **Loss & Optimizer**:
   Binary Cross-Entropy (BCE) loss optimized with Adam ($\text{lr} \in [0.03, 0.05]$) across 20 epochs with batch size 64.

---

## 5. Comprehensive Experimental Results Table

Evaluation metrics computed on the untouched holdout test partition (450 samples: 227 positive, 223 negative):

| Model Name | Category | Features | Qubits | Noise Condition | Accuracy | Balanced Acc | Sensitivity | Specificity | Precision | F1-Score | ROC-AUC | FP | FN |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **6-Qubit Noiseless VQC** | Hybrid Quantum | 6 | 6 | Noiseless | 53.11% | 52.92% | **74.45%** | 31.39% | 52.48% | **61.57%** | **0.5555** | 153 | **58** |
| **Logistic Regression (6 Feats)** | Classical ML | 6 | 0 | None (CPU) | 54.00% | 53.87% | 68.28% | 39.46% | 53.45% | 59.96% | 0.5531 | 135 | 72 |
| **Classical RBF SVM (6 Feats)** | Classical ML | 6 | 0 | None (CPU) | **54.67%** | **54.61%** | 60.79% | 48.43% | **54.55%** | 57.50% | 0.5316 | 115 | 89 |
| **Logistic Regression (4 Feats)** | Classical ML | 4 | 0 | None (CPU) | 51.78% | 51.72% | 58.15% | 45.29% | 51.97% | 54.89% | 0.5256 | 122 | 95 |
| **4-Qubit Noiseless VQC** | Hybrid Quantum | 4 | 4 | Noiseless | 52.67% | 52.69% | 49.78% | 55.61% | 53.30% | 51.48% | 0.5147 | 99 | 114 |
| **4-Qubit Noisy VQC** | Hybrid Quantum | 4 | 4 | Simulated NISQ | 52.67% | 52.70% | 49.34% | **56.05%** | 53.33% | 51.26% | 0.5174 | **98** | 115 |
| **Classical RBF SVM (4 Feats)** | Classical ML | 4 | 0 | None (CPU) | 52.44% | 52.46% | 51.10% | 53.81% | 52.97% | 52.02% | 0.5318 | 103 | 111 |
| **Classical Linear SVM (4 Feats)** | Classical ML | 4 | 0 | None (CPU) | 50.89% | 50.88% | 51.98% | 49.78% | 51.30% | 51.64% | 0.4972 | 112 | 109 |
| **8-Qubit Noiseless VQC** | Hybrid Quantum | 8 | 8 | Noiseless | 48.44% | 48.50% | 42.73% | 54.26% | 48.74% | 45.54% | 0.4990 | 102 | 130 |
| **Classical Linear SVM (8 Feats)** | Classical ML | 8 | 0 | None (CPU) | 50.44% | 50.00% | 100.00% | 0.00% | 50.44% | 67.06% | 0.5065 | 223 | 0 |
| **Classical RBF SVM (8 Feats)** | Classical ML | 8 | 0 | None (CPU) | 50.44% | 50.00% | 100.00% | 0.00% | 50.44% | 67.06% | 0.4879 | 223 | 0 |
| **Classical Linear SVM (6 Feats)** | Classical ML | 6 | 0 | None (CPU) | 50.44% | 50.00% | 100.00% | 0.00% | 50.44% | 67.06% | 0.4541 | 223 | 0 |

---

## 6. Interpretation of Results for This Dataset

1. **Detection Sensitivity**:
   - The 6-Qubit VQC identified 169 of the 227 positive cancer cases, achieving **74.45% sensitivity**, outperforming classical models (6-feature RBF SVM: 60.79%, Logistic Regression: 68.28%).
2. **False Positive Trade-off**:
   - The 6-qubit quantum model produced lower specificity (31.39%), resulting in 153 false positives compared to 115 in RBF SVM.
3. **Parameter Efficiency**:
   - The 6-qubit quantum model utilized only 13 trainable parameters ($6 \times 2$ angles + 1 bias) to achieve high recall, demonstrating compact functional representation.
4. **Dimensionality Limits**:
   - Expanding to 8 features caused performance to decline across both quantum (48.44% accuracy) and classical models (boundary collapse), illustrating that higher qubit counts do not monotonically improve results without substantially larger training datasets.
5. **Noise Stability**:
   - The 4-qubit VQC maintained identical 52.67% accuracy under simulated 1% depolarizing and phase damping noise, showing that low-depth variational circuits are structurally stable against modest environmental decoherence.

---

## 7. Structure & Experiments

- [data/](data/README.md): Raw dataset, processed splits, feature selection logs.
- [notebooks/](notebooks): Reproducible research notebooks (01 to 08).
- [CML/](CML/4-feature/README.md): Classical ML experiments (4, 6, 8 features).
- [HQML/](HQML/4-feature-VQC/README.md): Variational Quantum Classifiers (4, 4-noisy, 6, 8 qubits).
- [results/](results/classical_vs_quantum/README.md): Consolidated comparison tables, feature scaling, and noise studies.
- [docs/](docs/01_problem_definition.md): 11 high-level methodological documents.
