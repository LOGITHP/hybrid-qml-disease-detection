# Classical Machine Learning: 8-Feature Experiment

## 1. Objective
This experiment investigates the behavior of classical models when expanding the input representation to 8 features. It serves as the direct classical comparator for the 8-qubit Variational Quantum Classifier (VQC). The primary objective is to evaluate whether further feature expansion improves generalization or induces boundary instability on the held-out test set.

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
- **Why this feature configuration is being evaluated**: Selected through Sequential Forward Selection targeting 8 clinical attributes to match an 8-qubit quantum state space ($2^8 = 256$ complex state dimensions).

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
Raw data → cleaning & deduplication → binary mapping & MinMaxScaler on continuous Age → SFS 8-feature extraction (`X_train_8.csv`, `X_validation_8.csv`, `X_test_8.csv`) → model training.

## 5. Model Configuration
- **Models Evaluated**:
  - Classical Linear SVM (`C=0.01`, class_weight=None)
  - Classical RBF SVM (`C=0.1`, `gamma=0.05`, class_weight=None)
- **Feature count**: 8

## 6. Results

Evaluation metrics computed on the untouched holdout test set (450 samples):

| Metric | Linear SVM (8 Feats) | RBF SVM (8 Feats) |
|---|---:|---:|
| Accuracy | 50.44% | 50.44% |
| Balanced Accuracy | 50.00% | 50.00% |
| Sensitivity (Recall) | 100.00% | 100.00% |
| Specificity | 0.00% | 0.00% |
| Precision | 50.44% | 50.44% |
| F1-Score | 67.06% | 67.06% |
| ROC-AUC | 0.5065 | 0.4879 |
| True Positives | 227 | 227 |
| False Positives | 223 | 223 |
| True Negatives | 0 | 0 |
| False Negatives | 0 | 0 |

## 7. Figures
- [Figure directory](CML/8-feature/figures)
- [Quantum Scaling Comparison 4-6-8](CML/8-feature/figures/quantum_scaling_comparison_4_6_8.png)

## 8. Simple Interpretation
- **Accuracy**: Both Linear and RBF SVM yielded 50.44% accuracy on the test set, reflecting trivial majority prediction under standard penalty settings.
- **Sensitivity**: 100.00%, because all 227 positive samples were classified as positive.
- **Specificity**: 0.00%, meaning none of the 223 negative samples were correctly identified (all were predicted as positive).
- **ROC-AUC**: 0.5065 for Linear SVM and 0.4879 for RBF SVM, indicating near-random discriminative ordering across decision margins.
- **Interpretation**: Expanding to 8 features without re-weighting or threshold optimization caused standard SVM formulations to collapse toward predicting the positive class. More features do not automatically translate to better classical performance without careful regularization.

## 9. Limitations
- Vulnerability to decision threshold collapse when classes have high symptom overlap.
- High dimensionality relative to signal-to-noise ratio in survey-based clinical predictors.

## 10. Conclusion
The 8-feature classical SVM models illustrate the risk of feature expansion without adaptive regularization, resulting in boundary saturation. This baseline provides an important contrast for evaluating how quantum Hilbert space expansion behaves under identical 8-feature inputs.
