# Hybrid Quantum Machine Learning: 8-Feature Noiseless VQC Experiment

## 1. Objective
This experiment scales the Variational Quantum Classifier to 8 qubits, operating in a $2^8 = 256$-dimensional complex Hilbert state space. It evaluates how quantum expressibility scales when adding more features and entangling gates, testing whether high qubit counts translate to better classification performance or encounter optimization bottlenecks like barren plateaus.

## 2. Feature Configuration
- **Number of features**: 8
- **Feature names**:
  1. `COUGHING`
  2. `PEER_PRESSURE`
  3. `AGE`
  4. `ANXIETY`
  5. `ALLERGY`
  6. `SHORTNESS_OF_BREATH`
  7. `CHEST_PAIN`
  8. `CHRONIC_DISEASE`
- **Why this feature configuration is being evaluated**: Selected via Sequential Forward Selection to evaluate high-dimensional quantum representations matching 8 wires.

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
Raw data → cleaning & deduplication → binary mapping & MinMaxScaler continuous Age → 8 selected features extracted (`X_train_8.csv`, `X_validation_8.csv`, `X_test_8.csv`) → Angle Embedding $\text{RY}(x_i \cdot \pi)$ across 8 qubits → 2-layer 8-qubit VQC model.

## 5. Model Configuration
- **Qubits**: 8
- **Encoding**: Angle Embedding via single-qubit rotations $\text{RY}(x_i \cdot \pi)$ for $i \in \{0 \dots 7\}$
- **Ansatz**: 2-Layer parameterized circuit with $\text{RY}(\theta)$ rotations and linear CNOT ladder ($0 \to 1 \to \dots \to 7$)
- **Layers**: 2 layers
- **Trainable parameters**: $8 \times 2 = 16$ quantum angles + 1 classical bias = 17 parameters
- **Optimizer**: Adam (learning rate = 0.03)
- **Epochs**: 20
- **Batch Size**: 64
- **Backend / Simulator**: PennyLane `default.qubit` (analytic statevector)
- **Noise configuration**: Noiseless analytic simulation

## 6. Results

Evaluation metrics computed on the untouched holdout test set (450 samples):

| Metric | Value |
|---|---:|
| Accuracy | 48.44% |
| Balanced Accuracy | 48.50% |
| Sensitivity (Recall) | 42.73% |
| Specificity | 54.26% |
| Precision | 48.74% |
| F1-score | 45.54% |
| ROC-AUC | 0.4990 |
| True Positives | 97 |
| False Positives | 102 |
| True Negatives | 121 |
| False Negatives | 130 |

## 7. Figures
- [Circuit Diagram](HQML/8-feature-VQC/figures/vqc_8_circuit_diagram.png)
- [Training Loss Progression](HQML/8-feature-VQC/figures/vqc_8_training_curves.png)
- [Confusion Matrix](HQML/8-feature-VQC/figures/vqc_8_confusion_matrix.png)
- [ROC Curve](HQML/8-feature-VQC/figures/vqc_8_roc_curve.png)
- [Quantum Scaling Comparison 4-6-8](HQML/8-feature-VQC/figures/quantum_scaling_comparison_4_6_8.png)

## 8. Simple Interpretation
- **Accuracy**: Accuracy decreased to 48.44%, falling below both the 4-qubit (52.67%) and 6-qubit (53.11%) models.
- **Sensitivity**: The model detected 42.73% of positive cases (97 out of 227), missing 130 cases.
- **Specificity**: Specificity was 54.26% (121 out of 223 negative cases).
- **ROC-AUC**: Evaluated at 0.4990, hovering right around the 0.50 line of uninformative prediction.
- **Interpretation**: Expanding the quantum register to 8 qubits ($256$ complex state dimensions) did not improve performance. Instead, performance degraded compared to the 6-qubit model. In quantum machine learning, larger Hilbert spaces do not automatically guarantee superior generalization; without extensive sample sizes, higher qubit counts can dilute gradient magnitudes or lead to optimization plateaus.

## 9. Limitations
- Potential susceptibility to gradient vanishing / barren plateau tendencies in higher-dimensional ansatzes.
- Increased simulation runtime and parameter space relative to available survey dataset signal.

## 10. Conclusion
The 8-qubit VQC experiment experimentally demonstrated that adding qubits does not monotonically improve classification. The 6-qubit architecture remains the sweet spot in this feature-scaling study, balancing expressibility against parameter trainability.
