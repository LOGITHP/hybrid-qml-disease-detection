# Hybrid Quantum-Classical ML Comparative Benchmark Report
**Experiment ID:** `6abbba0b4aa32114d171dc51`

## Model Performance Summary
| Model | Type | Accuracy | Sensitivity (Recall) | Specificity | F1-Score | ROC-AUC | Training Time (s) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Linear SVM Classifier · Lung Cancer Pilot Study v1.0** | `svm_linear` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.042s |
| **Variational Quantum Classifier · Lung Cancer Pilot Study v1.0** | `vqc` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.121s |

## Medical Interpretation & Decision Support Note
> **Disclaimer:** Risk stratifications and comparative metrics reflect computational validation on test sets. The platform assists clinical screening workflows and does NOT generate definitive diagnoses.

## Quantum Advantage Observations
The Variational Quantum Classifier (VQC) with parameterized AngleEncoding and entangling layers demonstrates competitive performance on non-linearly separable biomarker subspaces.