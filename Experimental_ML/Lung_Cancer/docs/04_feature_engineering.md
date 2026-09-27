# 04. Feature Engineering & Multi-Criterion Selection Strategy

## 1. Motivation for Compact Feature Subsets
In Variational Quantum Computing on NISQ simulators and physical backends, qubit counts and gate depths are tightly constrained. Simulating high-qubit circuits incurs exponential statevector memory overhead ($2^n$ complex amplitudes), while physical processors suffer from accumulated gate decoherence. Therefore, dimensionality compression from 15 candidate predictors to compact subsets of 4, 6, and 8 features is essential.

## 2. Multi-Criterion Relevance Screening
Feature selection was conducted strictly on the 2,098 training samples using three complementary ranking criteria:
1. **Mutual Information (`mutual_info_classif`)**: Quantifies non-linear statistical dependency between each feature and the diagnosis without assuming linearity.
2. **Univariate ANOVA F-statistic (`f_classif`)**: Assesses linear separation of class means.
3. **Random Forest Gini Importance**: Measures average reduction in node impurity across an ensemble of 100 decision trees.

## 3. Sequential Forward Selection (SFS) Trajectory
Using validation balanced accuracy as the objective metric, Sequential Forward Selection iteratively added candidate features:
- **Step 1**: `COUGHING` was selected first, providing the highest individual balanced accuracy.
- **Step 2**: `PEER_PRESSURE` added, capturing environmental and behavioral exposure.
- **Step 3**: `AGE` added, incorporating the continuous demographic risk curve.
- **Step 4**: `YELLOW_FINGERS` added, reinforcing chronic smoking indications.
- **Step 5**: `SHORTNESS_OF_BREATH` added, contributing lower respiratory distress information.
- **Step 6**: `CHEST_PAIN` added, completing the 6-feature subset.
- **Steps 7-8**: `ANXIETY`, `ALLERGY`, and `CHRONIC_DISEASE` added, forming the 8-feature representation.

## 4. Final Standardized Feature Subsets

| Subset | Dimension | Selected Clinical Attributes | Rationale |
|---|---:|---|---|
| **4-Feature** | 4 | `WHEEZING`, `YELLOW_FINGERS`, `AGE`, `SHORTNESS_OF_BREATH` | Minimal viable register for 4-qubit quantum simulation ($2^4 = 16$ Hilbert dimensions). |
| **6-Feature** | 6 | `COUGHING`, `PEER_PRESSURE`, `AGE`, `YELLOW_FINGERS`, `SHORTNESS_OF_BREATH`, `CHEST_PAIN` | SFS-optimized representation balancing expressiveness and circuit depth ($2^6 = 64$ dimensions). |
| **8-Feature** | 8 | `COUGHING`, `PEER_PRESSURE`, `AGE`, `ANXIETY`, `ALLERGY`, `SHORTNESS_OF_BREATH`, `CHEST_PAIN`, `CHRONIC_DISEASE` | High-dimensional test case for quantum state space scaling ($2^8 = 256$ dimensions). |
