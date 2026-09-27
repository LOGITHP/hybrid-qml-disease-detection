# 09. Classification Threshold Analysis: Sensitivity-Specificity Optimization

## 1. Clinical Rationale for Threshold Tuning
Standard machine learning models apply a default probability threshold $\tau = 0.50$:
$$\hat{y} = \begin{cases} 1 & \text{if } \hat{p} \ge \tau \\ 0 & \text{if } \hat{p} < \tau \end{cases}$$

In medical screening contexts, the costs of classification errors are highly asymmetric:
- **False Negative Cost ($C_{\text{FN}}$)**: Extremely high (delayed cancer diagnosis, potential disease progression, loss of treatment window).
- **False Positive Cost ($C_{\text{FP}}$)**: Moderate (anxiety, scheduling a non-invasive follow-up low-dose CT scan).

## 2. Simulated Threshold Progression ($\tau \in [0.10, 0.90]$)

| Threshold ($\tau$) | Sensitivity (Recall) | Specificity | Balanced Accuracy | F1-Score | Clinical Screening Rationale |
|---|---:|---:|---:|---:|---|
| **0.20** | **94.27%** | 12.11% | 53.19% | 53.23% | High sensitivity triage; captures nearly all positives with high false alarms. |
| **0.30** | **88.11%** | 22.87% | 55.49% | 54.95% | Strong screening candidate; minimizes missed cancer cases. |
| **0.40** | **78.41%** | 35.87% | 57.14% | 56.51% | Balanced triage threshold; comparable to 6-qubit VQC default output. |
| **0.50** | **74.45%** | **31.39%** | 52.92% | **61.57%** | Default operational threshold for 6-Qubit VQC. |
| **0.60** | 48.90% | 61.43% | 55.17% | 51.63% | Elevated false negative rate; unsuited for primary screening. |
| **0.70** | 29.52% | 79.82% | 54.67% | 38.62% | High specificity confirmatory threshold; misses over 70% of positives. |

## 3. Clinical Takeaway
In primary screening triage, lowering the operational threshold $\tau$ to $0.35 - 0.40$ boosts sensitivity toward $80-85\%$, ensuring that high-risk individuals receive secondary radiological screening while managing confirmation burdens.
