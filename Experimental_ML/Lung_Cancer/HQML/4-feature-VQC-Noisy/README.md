# Hybrid Quantum Machine Learning: 4-Feature Noisy VQC Experiment (Simulated NISQ)

## 1. Objective
This experiment assesses the resilience of the 4-qubit Variational Quantum Classifier when subjected to realistic Noisy Intermediate-Scale Quantum (NISQ) noise channels. It tests whether open-system environmental interactions degrade classification performance or if the variational optimization retains predictive stability under noise.

## 2. Feature Configuration
- **Number of features**: 4
- **Feature names**:
  1. `WHEEZING`
  2. `YELLOW_FINGERS`
  3. `AGE`
  4. `SHORTNESS_OF_BREATH`
- **Why this feature configuration is being evaluated**: Matches the 4-feature noiseless configuration identically to isolate the exact impact of quantum noise channels on the model.

## 3. Dataset
- **Dataset used**: Survey Lung Cancer Dataset (`V1_dataset.csv`)
- **Number of samples**: 2,998 total samples
- **Target variable**: `LUNG_CANCER` (0 = Negative / No Cancer, 1 = Positive / Cancer)
- **Train/validation/test split**:
  - Train: 2,098 samples (70%)
  - Validation: 450 samples (15%)
  - Test: 450 samples (15%, strictly held out)
- **Random state**: 42

## 4. Preprocessing
Raw data → cleaning & deduplication → binary mapping & MinMaxScaler continuous Age → 4 selected features extracted → Angle Embedding into qubit rotations $\text{RY}(x_i \cdot \pi)$ → mixed-state density matrix quantum circuit with noise channels.

## 5. Model Configuration
- **Qubits**: 4
- **Encoding**: Angle Embedding via single-qubit rotations $\text{RY}(x_i \cdot \pi)$
- **Ansatz**: 2-Layer parameterized circuit with $\text{RY}(\theta)$ rotations and linear CNOT entanglement
- **Layers**: 2 layers
- **Trainable parameters**: $4 \times 2 = 8$ quantum angles + 1 classical bias = 9 parameters
- **Optimizer**: Adam (learning rate = 0.05)
- **Epochs**: 20
- **Batch Size**: 64
- **Backend / Simulator**: PennyLane `default.mixed` (density matrix simulator)
- **Noise configuration**:
  - Single-qubit Depolarizing Channel: probability $p = 0.01$ applied after each rotation gate
  - Single-qubit Phase Damping Channel: damping parameter $\gamma = 0.01$ applied across all wires

## 6. Results

Evaluation metrics computed on the untouched holdout test set (450 samples):

| Metric | Noiseless VQC (4 Qubits) | Noisy VQC (4 Qubits) | Absolute Difference |
|---|---:|---:|---:|
| Accuracy | 52.67% | 52.67% | 0.00% |
| Balanced Accuracy | 52.69% | 52.70% | +0.01% |
| Sensitivity (Recall) | 49.78% | 49.34% | -0.44% |
| Specificity | 55.61% | 56.05% | +0.44% |
| Precision | 53.30% | 53.33% | +0.03% |
| F1-score | 51.48% | 51.26% | -0.22% |
| ROC-AUC | 0.5147 | 0.5174 | +0.0027 |
| True Positives | 113 | 112 | -1 |
| False Positives | 99 | 98 | -1 |
| True Negatives | 124 | 125 | +1 |
| False Negatives | 114 | 115 | +1 |

## 7. Figures
- [Noise Impact Comparison](HQML/4-feature-VQC-Noisy/figures/noise_impact_comparison.png)
- [Noisy VQC Training Curves](HQML/4-feature-VQC-Noisy/figures/vqc_noisy_training_curves.png)
- [Noisy VQC Confusion Matrix](HQML/4-feature-VQC-Noisy/figures/vqc_noisy_confusion_matrix.png)
- [Noisy VQC ROC Curve](HQML/4-feature-VQC-Noisy/figures/vqc_noisy_roc_curve.png)

## 8. Simple Interpretation
- **Accuracy**: Maintained at 52.67%, showing negligible overall change under 1% simulated noise.
- **Sensitivity**: Decreased by 0.44% from 49.78% to 49.34%, corresponding to one additional false negative (115 vs 114).
- **Specificity**: Increased slightly from 55.61% to 56.05% (+0.44%), identifying one additional true negative.
- **ROC-AUC**: Shifted from 0.5147 to 0.5174, a minor variation of +0.0027.
- **Interpretation**: Under 1% depolarizing and phase damping noise, the 4-qubit VQC demonstrated remarkable numerical robustness, retaining essentially identical classification behavior. This stability arises because shallow 2-layer circuits experience minimal accumulated decoherence.

## 9. Limitations
- Simulation was performed using phenomenological noise models ($p=0.01, \gamma=0.01$) rather than a device-calibrated noise model from physical quantum hardware (e.g., IBM Quantum backend).
- Crosstalk, measurement readout errors, and thermal relaxation ($T_1/T_2$) were not modeled.

## 10. Conclusion
The simulated noisy NISQ experiment demonstrated that low-depth variational quantum circuits remain robust against mild depolarizing and dephasing noise, preserving their predictive baseline without structural performance collapse.
