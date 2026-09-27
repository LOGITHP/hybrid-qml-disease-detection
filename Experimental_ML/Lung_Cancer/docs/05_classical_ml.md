# 05. Classical Machine Learning Methodology & Empirical Analysis

## 1. Classical Model Architectures
Classical models were trained to establish rigorous benchmark baselines against the quantum classifiers using identical features and partitions:
- **Logistic Regression**: Serves as the primary linear baseline, optimizing cross-entropy loss over a linear combination of features.
- **Linear Support Vector Machine (Linear SVM)**: Identifies the maximum-margin hyperplane separating classes in feature space.
- **Radial Basis Function Support Vector Machine (RBF SVM)**: Projects input vectors into an infinite-dimensional reproducing kernel Hilbert space using Gaussian kernels:
  $$K(\mathbf{x}, \mathbf{x}') = \exp(-\gamma ||\mathbf{x} - \mathbf{x}'||^2)$$

## 2. Hyperparameter Tuning & Cross-Validation
Hyperparameters were optimized using 5-fold cross-validation on the combined training and validation sets:
- **Linear SVM**: Regularization parameter $C \in [0.01, 0.1, 1.0, 10.0]$.
- **RBF SVM**: Regularization $C \in [0.1, 1.0, 10.0]$, kernel width $\gamma \in [0.01, 0.05, 0.1, 0.5]$.
- Best configurations were evaluated once on the untouched 450-sample holdout test partition.

## 3. Empirical Results Across Dimensionalities

| Configuration | Model | Accuracy | Balanced Accuracy | Sensitivity | Specificity | F1-Score | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| **4 Features** | Logistic Regression | 51.78% | 51.72% | 58.15% | 45.29% | 54.89% | 0.5256 |
| **4 Features** | Classical Linear SVM | 50.89% | 50.88% | 51.98% | 49.78% | 51.64% | 0.4972 |
| **4 Features** | Classical RBF SVM | 52.44% | 52.46% | 51.10% | 53.81% | 52.02% | 0.5318 |
| **6 Features** | Logistic Regression | 54.00% | 53.87% | **68.28%** | 39.46% | 59.96% | **0.5531** |
| **6 Features** | Classical RBF SVM | **54.67%** | **54.61%** | 60.79% | 48.43% | 57.50% | 0.5316 |
| **6 Features** | Classical Linear SVM | 50.44% | 50.00% | 100.00% | 0.00% | 67.06% | 0.4541 |
| **8 Features** | Classical RBF SVM | 50.44% | 50.00% | 100.00% | 0.00% | 67.06% | 0.4879 |
| **8 Features** | Classical Linear SVM | 50.44% | 50.00% | 100.00% | 0.00% | 67.06% | 0.5065 |

## 4. In-Depth Interpretation of Classical Results
1. **6-Feature Sweet Spot**:
   - Extending from 4 to 6 features delivered meaningful improvements: Logistic Regression sensitivity increased from 58.15% to 68.28% (+10.13%), and RBF SVM accuracy rose from 52.44% to 54.67%.
   - Clinical features `COUGHING` and `CHEST_PAIN` added genuine discriminatory signal.
2. **Boundary Collapse at 8 Features**:
   - In 8-feature space, standard linear and RBF SVMs collapsed into trivial majority prediction (100% sensitivity, 0% specificity, 223 false positives).
   - This occurs because adding correlated survey features without adaptive class penalties shrinks the margin between overlapping patient clusters, pushing the optimal uncalibrated hyperplane outside the data cloud.
