# Feature-Set Dimensionality & Scaling Analysis: 4 vs. 6 vs. 8 Features

## 1. Objective
This analysis investigates the empirical impact of feature dimensionality scaling across both classical algorithms and variational quantum classifiers. By comparing 4-feature, 6-feature, and 8-feature pipelines, we examine how state space expansion ($2^4 \to 2^6 \to 2^8$) and additional clinical predictors influence model performance and trainability.

## 2. Feature Configurations

| Configuration | Feature Count | Qubits | Hilbert Space Dimension | Trainable Quantum Parameters | Selected Clinical Features |
|---|---:|---:|---:|---:|---|
| **4-Feature** | 4 | 4 | 16 ($2^4$) | 9 | `WHEEZING`, `YELLOW_FINGERS`, `AGE`, `SHORTNESS_OF_BREATH` |
| **6-Feature** | 6 | 6 | 64 ($2^6$) | 13 | `COUGHING`, `PEER_PRESSURE`, `AGE`, `YELLOW_FINGERS`, `SHORTNESS_OF_BREATH`, `CHEST_PAIN` |
| **8-Feature** | 8 | 8 | 256 ($2^8$) | 17 | `COUGHING`, `PEER_PRESSURE`, `AGE`, `ANXIETY`, `ALLERGY`, `SHORTNESS_OF_BREATH`, `CHEST_PAIN`, `CHRONIC_DISEASE` |

## 3. Comparative Performance Across Dimensionalities

### Quantum (VQC) Progression:
- **4 Qubits (16 dims, 9 params)**:
  - Accuracy: 52.67% | Balanced Acc: 52.69% | Sensitivity: 49.78% | Specificity: 55.61% | ROC-AUC: 0.5147
- **6 Qubits (64 dims, 13 params)**:
  - Accuracy: 53.11% | Balanced Acc: 52.92% | **Sensitivity: 74.45%** | Specificity: 31.39% | **ROC-AUC: 0.5555**
- **8 Qubits (256 dims, 17 params)**:
  - Accuracy: 48.44% | Balanced Acc: 48.50% | Sensitivity: 42.73% | Specificity: 54.26% | ROC-AUC: 0.4990

### Classical ML Progression (RBF SVM & Logistic Regression):
- **4 Features**:
  - RBF SVM: Accuracy 52.44%, Sensitivity 51.10%, Specificity 53.81%, ROC-AUC 0.5318
  - Logistic Regression: Accuracy 51.78%, Sensitivity 58.15%, Specificity 45.29%, ROC-AUC 0.5256
- **6 Features**:
  - RBF SVM: Accuracy 54.67%, Sensitivity 60.79%, Specificity 48.43%, ROC-AUC 0.5316
  - Logistic Regression: Accuracy 54.00%, Sensitivity 68.28%, Specificity 39.46%, ROC-AUC 0.5531
- **8 Features**:
  - RBF SVM: Accuracy 50.44%, Sensitivity 100.00%, Specificity 0.00% (collapsed boundary), ROC-AUC 0.4879
  - Linear SVM: Accuracy 50.44%, Sensitivity 100.00%, Specificity 0.00% (collapsed boundary), ROC-AUC 0.5065

## 4. Analysis and Findings

1. **Non-Monotonic Relationship**: Adding more features or more qubits did **not** automatically produce better results. Performance rose from 4 to 6 features, but subsequently declined at 8 features across both quantum and classical architectures.
2. **6-Feature Optimal Trade-off**: The 6-feature configuration represents the most effective trade-off in this benchmark:
   - For VQC, sensitivity increased from 49.78% to 74.45% (+24.67 percentage points), and ROC-AUC improved from 0.5147 to 0.5555.
   - For classical models, Logistic Regression sensitivity rose from 58.15% to 68.28%, and RBF SVM accuracy rose from 52.44% to 54.67%.
3. **8-Feature Degradation**:
   - In the 8-qubit VQC, operating in a 256-dimensional Hilbert space with 17 parameters resulted in lower sensitivity (42.73%) and an ROC-AUC of 0.4990, reflecting optimization challenges in higher dimensions with limited training samples.
   - In classical SVMs, 8 features without modified hyperparameter penalties caused the decision boundary to collapse to predicting positive for all samples.

## 5. Conclusion
Empirical evidence refutes the assumption that larger qubit counts or expanded feature sets monotonically improve model accuracy. The 6-feature / 6-qubit architecture emerged as the most informative representation in this experimental dataset.
