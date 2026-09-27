# Classical Machine Learning: 4-Feature Experiment

## 1. Objective
This experiment evaluates the baseline performance of classical machine learning algorithms trained on a compact 4-feature subset for lung cancer classification. It establishes a benchmark to compare classical linear and non-linear boundaries against low-dimensional quantum circuits. The goal is to observe whether four clinical indicators provide sufficient predictive information for classical classifiers on a held-out test set.

## 2. Feature Configuration
- **Number of features**: 4
- **Feature names**:
  1. `WHEEZING`
  2. `YELLOW_FINGERS`
  3. `AGE`
  4. `SHORTNESS_OF_BREATH`
- **Why this feature configuration is being evaluated**: This 4-feature subset was identified during initial feature screening to match a minimal 4-qubit quantum circuit constraints, selecting high-ranking clinical variables based on mutual information and univariate correlation.

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
The preprocessing follows a strict leakage-free pipeline:
Raw data → cleaning & deduplication → binary encoding (Gender: M=1, F=0; Cancer: YES=1, NO=0; symptoms mapped from 1/2 to 0/1) → MinMaxScaler on continuous Age → 4 selected features extracted → model training.

## 5. Model Configuration
- **Models Evaluated**:
  - Logistic Regression (Trainable params: 5, solver: lbfgs)
  - Linear Support Vector Machine (`C=0.01`, class_weight=None)
  - Radial Basis Function (RBF) SVM (`C=0.1`, `gamma=0.05`, class_weight=None)
- **Feature count**: 4

## 6. Results

Evaluation metrics computed on the untouched holdout test set (450 samples):

| Metric | Logistic Regression (4 Feats) | Linear SVM (4 Feats) | RBF SVM (4 Feats) |
|---|---:|---:|---:|
| Accuracy | 51.78% | 50.89% | 52.44% |
| Balanced Accuracy | 51.72% | 50.88% | 52.46% |
| Sensitivity (Recall) | 58.15% | 51.98% | 51.10% |
| Specificity | 45.29% | 49.78% | 53.81% |
| Precision | 51.97% | 51.30% | 52.97% |
| F1-Score | 54.89% | 51.64% | 52.02% |
| ROC-AUC | 0.5256 | 0.4972 | 0.5318 |
| True Positives | 132 | 118 | 116 |
| False Positives | 122 | 112 | 103 |
| True Negatives | 101 | 111 | 120 |
| False Negatives | 95 | 109 | 111 |

## 7. Figures
The generated performance figures for classical models are archived in the figures directory:
- [Figure directory](CML/4-feature/figures)
- [Sensitivity Comparison Figure](CML/4-feature/figures/04_svm_vs_vqc_sensitivity_comparison.png)

## 8. Simple Interpretation
- **Accuracy** measures the percentage of correctly classified samples across both classes. The highest accuracy observed among the 4-feature classical models was 52.44% by RBF SVM.
- **Sensitivity** measures the proportion of actual positive cancer cases correctly identified by the model. Logistic Regression achieved a sensitivity of 58.15%, identifying 132 of the 227 positive cases.
- **Specificity** measures how many actual negative cases were correctly identified. RBF SVM achieved 53.81%, while Logistic Regression achieved 45.29%.
- **ROC-AUC** evaluates the ranking ability across decision thresholds. The scores ranged from 0.4972 to 0.5318, which is close to the baseline chance level of 0.50.
- **Interpretation**: With only 4 features, classical linear and non-linear classifiers struggle to separate the classes effectively, yielding performance slightly above random guessing on the balanced holdout test set.

## 9. Limitations
- The 4-feature subset omits potentially informative clinical predictors like coughing, chest pain, and smoking history.
- Linear and RBF boundaries in 4 dimensions have limited capacity to resolve overlapping patient symptom profiles.
- Class distribution in test set has near parity, revealing that high default sensitivity comes at the cost of high false positives.

## 10. Conclusion
The 4-feature classical ML baseline demonstrates modest predictive capacity (accuracy ~51-52%, ROC-AUC ~0.50-0.53). This highlights the difficulty of diagnosing lung cancer status from four survey symptoms alone and serves as a direct baseline for the 4-qubit VQC experiment.
