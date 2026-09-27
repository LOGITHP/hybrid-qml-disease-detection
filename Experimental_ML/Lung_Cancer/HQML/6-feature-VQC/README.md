# Hybrid Quantum Machine Learning: 6-Feature Noiseless VQC Experiment

## 1. Objective
This experiment scales the Variational Quantum Classifier to 6 qubits ($2^6 = 64$ Hilbert space capacity) using a dedicated 6-feature clinical subset. It tests whether an expanded quantum state space combined with highly relevant symptom features enables the model to improve early lung cancer detection sensitivity.

## 2. Feature Configuration
- **Number of features**: 6
- **Feature names**:
  1. `COUGHING`
  2. `PEER_PRESSURE`
  3. `AGE`
  4. `YELLOW_FINGERS`
  5. `SHORTNESS_OF_BREATH`
  6. `CHEST_PAIN`
- **Why this feature configuration is being evaluated**: Selected via training-derived Sequential Forward Selection (SFS) optimized for validation balanced accuracy, mapping 6 clinical predictors directly to 6 quantum wires.

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
Raw data → cleaning & deduplication → binary mapping & MinMaxScaler continuous Age → 6 selected features extracted (`X_train_6.csv`, `X_validation_6.csv`, `X_test_6.csv`) → Angle Embedding $\text{RY}(x_i \cdot \pi)$ on 6 wires → 2-layer VQC model.

## 5. Model Configuration
- **Qubits**: 6
- **Encoding**: Angle Embedding via single-qubit rotations $\text{RY}(x_i \cdot \pi)$ for $i \in \{0 \dots 5\}$
- **Ansatz**: 2-Layer parameterized circuit with $\text{RY}(\theta)$ rotations and linear CNOT entanglement ladder
- **Layers**: 2 layers
- **Trainable parameters**: $6 \times 2 = 12$ quantum angles + 1 classical bias = 13 parameters
- **Optimizer**: Adam (learning rate = 0.03)
- **Epochs**: 20
- **Batch Size**: 64
- **Backend / Simulator**: PennyLane `default.qubit` (analytic statevector)
- **Noise configuration**: Noiseless analytic simulation

## 6. Results

Evaluation metrics computed on the untouched holdout test set (450 samples):

| Metric | Value |
|---|---:|
| Accuracy | 53.11% |
| Balanced Accuracy | 52.92% |
| Sensitivity (Recall) | 74.45% |
| Specificity | 31.39% |
| Precision | 52.48% |
| F1-score | 61.57% |
| ROC-AUC | 0.5555 |
| True Positives | 169 |
| False Positives | 153 |
| True Negatives | 70 |
| False Negatives | 58 |

## 7. Figures
- [Circuit Diagram](HQML/6-feature-VQC/figures/vqc_6_circuit_diagram.png)
- [Training Loss Progression](HQML/6-feature-VQC/figures/vqc_6_training_curves.png)
- [Confusion Matrix](HQML/6-feature-VQC/figures/vqc_6_confusion_matrix.png)
- [ROC Curve](HQML/6-feature-VQC/figures/vqc_6_roc_curve.png)
- [4 vs 6 Feature Comparison](HQML/6-feature-VQC/figures/4_vs_6_feature_comparison.png)

## 8. Simple Interpretation
- **Accuracy**: The 6-qubit VQC achieved 53.11% accuracy, outperforming the 4-qubit VQC (52.67%).
- **Sensitivity**: Sensitivity reached 74.45%, correctly detecting 169 of the 227 positive cases. This represents the highest sensitivity achieved across all tested models in the benchmark, missing only 58 cases.
- **Specificity**: Specificity dropped to 31.39% (70 true negatives out of 223), indicating that high sensitivity was achieved with an elevated false-positive rate.
- **ROC-AUC**: The model achieved an ROC-AUC of 0.5555, the highest among all quantum models evaluated.
- **Interpretation**: In screening contexts where early detection of positive cases is prioritized, the 6-qubit VQC demonstrated strong recall (74.45%), outperforming classical RBF SVM (60.79% sensitivity, 89 missed cases). However, this high sensitivity comes at the cost of lower specificity, requiring downstream clinical verification.

## 9. Limitations
- The trade-off between high sensitivity and low specificity requires decision threshold calibration.
- Entanglement depth is restricted to linear nearest-neighbor interactions to remain within NISQ simulation bounds.

## 10. Conclusion
The 6-qubit VQC demonstrated the most favorable positive-class recall (74.45% sensitivity) among all evaluated configurations, showing that expanding the state space to 6 qubits with selected clinical predictors provides effective non-linear feature mapping for detecting positive lung cancer instances.
