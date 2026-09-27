# Overall Model Comparison: Classical Machine Learning vs. Hybrid Quantum Machine Learning

## 1. Overview
This directory synthesizes the experimental results from all classical machine learning (CML) and variational quantum classification (HQML) architectures evaluated on the held-out test set (450 samples). The comparison includes 4, 6, and 8-feature classical models alongside 4-qubit, 4-qubit noisy, 6-qubit, and 8-qubit quantum models.

## 2. Comparison Summary Table

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

## 3. Data Files
- [comparison.csv](results/classical_vs_quantum/comparison.csv): Machine-readable table containing all 12 evaluated model entries.
- [comparison.json](results/classical_vs_quantum/comparison.json): Structured JSON dataset of models and metrics.

## 4. Key Observations
1. **Sensitivity Peak in 6-Qubit VQC**: The 6-Qubit VQC achieved a sensitivity of 74.45% on the held-out test set, identifying 169 of the 227 positive cancer cases and missing only 58. For comparison, the 6-feature Classical RBF SVM achieved 60.79% sensitivity (89 missed cases), and Logistic Regression reached 68.28% (72 missed cases).
2. **Specificity Trade-off**: The higher sensitivity in the 6-qubit quantum model comes with a trade-off in specificity (31.39%), resulting in 153 false positives compared to 115 in RBF SVM.
3. **Parameter Efficiency**: The 6-qubit VQC utilized only 13 trainable parameters ($6 \times 2 = 12$ rotation angles + 1 classical bias), whereas classical models require continuous hyperplane weights or non-linear kernel supports over the full training sample space.
4. **Saturation at 8 Features**: Increasing to 8 features did not improve performance for either classical SVMs (which collapsed to boundary saturation) or the 8-qubit VQC (accuracy 48.44%, sensitivity 42.73%), highlighting that higher dimensionality can impede trainability without sufficient data volume.
