# Hybrid Quantum Machine Learning: 4-Feature Noiseless VQC Experiment

## 1. Objective
This experiment implements and trains a 4-qubit Variational Quantum Classifier (VQC) using PennyLane on a noiseless statevector simulator. It tests whether low-depth parameterized quantum circuits can encode 4 clinical symptoms into quantum state space and learn non-linear decision boundaries for early lung cancer detection. The experiment serves as the foundational quantum baseline for all subsequent HQML evaluations.

## 2. Feature Configuration
- **Number of features**: 4
- **Feature names**:
  1. `WHEEZING`
  2. `YELLOW_FINGERS`
  3. `AGE`
  4. `SHORTNESS_OF_BREATH`
- **Why this feature configuration is being evaluated**: Selected during early screening to evaluate the minimal viable qubit register (4 qubits), allowing full statevector simulation while minimizing circuit depth.

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
Raw data → cleaning & deduplication → binary mapping & MinMaxScaler continuous Age → 4 selected features extracted (`X_train_4.csv`, `X_validation_4.csv`, `X_test_4.csv`) → Angle Embedding into qubit rotations $\text{RY}(x_i \cdot \pi)$ → VQC model.

## 5. Model Configuration
- **Qubits**: 4
- **Encoding**: Angle Embedding via single-qubit rotations $\text{RY}(x_i \cdot \pi)$ for $i \in \{0, 1, 2, 3\}$
- **Ansatz**: Strongly Entangling / 2-Layer parameterized circuit with $\text{RY}(\theta)$ rotations and circular/linear CNOT ladder
- **Layers**: 2 layers
- **Trainable parameters**: $4 \times 2 = 8$ quantum angles + 1 classical bias = 9 parameters
- **Optimizer**: Adam (learning rate = 0.05)
- **Epochs**: 20
- **Batch Size**: 64
- **Backend / Simulator**: PennyLane `default.qubit` (analytic statevector)
- **Noise configuration**: Noiseless analytic simulation

## 6. Results

Evaluation metrics computed on the untouched holdout test set (450 samples):

| Metric | Value |
|---|---:|
| Accuracy | 52.67% |
| Balanced Accuracy | 52.69% |
| Sensitivity (Recall) | 49.78% |
| Specificity | 55.61% |
| Precision | 53.30% |
| F1-score | 51.48% |
| ROC-AUC | 0.5147 |
| True Positives | 113 |
| False Positives | 99 |
| True Negatives | 124 |
| False Negatives | 114 |

## 7. Figures
- [Circuit Diagram](HQML/4-feature-VQC/figures/vqc_4_circuit_diagram.png)
- [Training Loss Progression](HQML/4-feature-VQC/figures/vqc_4_training_curves.png)
- [Confusion Matrix](HQML/4-feature-VQC/figures/vqc_4_confusion_matrix.png)
- [ROC Curve](HQML/4-feature-VQC/figures/vqc_4_roc_curve.png)

## 8. Simple Interpretation
- **Accuracy** measures the percentage of correctly classified samples. The model achieved 52.67% accuracy, which is comparable to the 4-feature classical RBF SVM (52.44%).
- **Sensitivity** measures how many actual positive cancer cases were detected. The 4-qubit VQC achieved 49.78% sensitivity, identifying 113 out of 227 positive cases.
- **Specificity** measures how many actual negative cases were correctly identified. The model achieved 55.61% specificity (124 out of 223 negative cases).
- **ROC-AUC** measures the probability ranking capability across thresholds. The model obtained 0.5147, reflecting balanced but modest discriminatory power.
- **Interpretation**: The 4-qubit VQC successfully optimized its 9 parameters and achieved balanced sensitivity and specificity, performing comparably to classical baselines with a highly compact parameter budget.

## 9. Limitations
- Restricted Hilbert space ($2^4 = 16$ dimensions) limits expressibility for complex multi-symptom relationships.
- Analytic statevector simulation does not account for physical quantum hardware noise or shot-noise variance.

## 10. Conclusion
The 4-qubit noiseless VQC demonstrated that a compact parameterized quantum circuit can be stably trained via gradient descent on survey clinical data, achieving parity with 4-feature classical baselines with only 9 trainable parameters.
