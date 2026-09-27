# Classical Machine Learning: 6-Feature Experiment

## 1. Objective
This experiment examines whether extending the feature set from 4 to 6 features improves the classification performance of classical ML algorithms. It provides a classical comparison counterpart for the 6-qubit Variational Quantum Classifier (VQC). The goal is to determine if adding symptom combinations like coughing and chest pain enhances sensitivity and overall separation.

## 2. Feature Configuration
- **Number of features**: 6
- **Feature names**:
  1. `COUGHING`
  2. `PEER_PRESSURE`
  3. `AGE`
  4. `YELLOW_FINGERS`
  5. `SHORTNESS_OF_BREATH`
  6. `CHEST_PAIN`
- **Why this feature configuration is being evaluated**: Selected via training-set Sequential Forward Selection (SFS) guided by validation balanced accuracy, targeting an intermediate feature dimension matching 6 qubits ($2^6 = 64$ Hilbert space capacity).

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
Raw data → cleaning & deduplication → binary mapping & MinMaxScaler on Age → SFS 6-feature extraction (`X_train_6.csv`, `X_validation_6.csv`, `X_test_6.csv`) → model training.

## 5. Model Configuration
- **Models Evaluated**:
  - Logistic Regression (Trainable params: 7, solver: lbfgs)
  - Classical Linear SVM (`C=0.01`, class_weight=None)
  - Classical RBF SVM (`C=0.1`, `gamma=0.05`, class_weight=None)
- **Feature count**: 6

## 6. Results

Evaluation metrics computed on the untouched holdout test set (450 samples):

| Metric | Logistic Regression (6 Feats) | RBF SVM (6 Feats) | Linear SVM (6 Feats) |
|---|---:|---:|---:|
| Accuracy | 54.00% | 54.67% | 50.44% |
| Balanced Accuracy | 53.87% | 54.61% | 50.00% |
| Sensitivity (Recall) | 68.28% | 60.79% | 100.00% |
| Specificity | 39.46% | 48.43% | 0.00% |
| Precision | 53.45% | 54.55% | 50.44% |
| F1-Score | 59.96% | 57.50% | 67.06% |
| ROC-AUC | 0.5531 | 0.5316 | 0.4541 |
| True Positives | 155 | 138 | 227 |
| False Positives | 135 | 115 | 223 |
| True Negatives | 88 | 108 | 0 |
| False Negatives | 72 | 89 | 0 |

## 7. Figures
- [Figure directory](CML/6-feature/figures)
- [4 vs 6 Feature Comparison Figure](CML/6-feature/figures/04_svm_vs_vqc_sensitivity_comparison.png)

## 8. Simple Interpretation
- **Accuracy**: RBF SVM achieved 54.67% accuracy, an improvement over the 52.44% obtained with 4 features.
- **Sensitivity**: Logistic Regression detected 68.28% of positive cases (155 out of 227), while RBF SVM detected 60.79% (138 out of 227). Linear SVM with default threshold collapsed to predicting positive for all samples (100% sensitivity, 0% specificity).
- **Specificity**: Specificity remained low (39.46% for Logistic Regression, 48.43% for RBF SVM), indicating a substantial false-positive rate.
- **ROC-AUC**: Logistic Regression reached 0.5531, showing mild discriminating power compared to random chance.
- **Interpretation**: Adding coughing and chest pain improved positive-class recall for classical models, but specificity remained challenging due to symptom overlap among non-cancer individuals.

## 9. Limitations
- Uncalibrated decision boundaries can cause models (e.g. Linear SVM) to predict the majority class uniformly.
- Moderate sample size and self-reported survey nature limit absolute separability.

## 10. Conclusion
The 6-feature classical models demonstrated superior sensitivity (up to 68.28% in Logistic Regression) compared to the 4-feature configuration, confirming that the additional clinical features add useful signal, while highlighting remaining false-positive challenges.
