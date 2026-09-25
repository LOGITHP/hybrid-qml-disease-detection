# Comprehensive Dataset Analysis Report
## Project: Hybrid Quantum Machine Learning Platform for Early Disease Detection
**Stage:** 01 — Raw Dataset Analysis & Pipeline Feasibility Audit  
**Target Variable:** `LUNG_CANCER`  
**Dataset File:** `V1_dataset.csv`  
**Audience:** ML/QML Engineers, Clinical Researchers, and Smart India Hackathon (SIH) Evaluation Jury  

---

### Executive Summary
This report provides a formal, comprehensive exploratory audit of the raw clinical screening dataset (`V1_dataset.csv`) for the Hybrid Quantum Machine Learning (HQML) Disease Detection Platform. All investigations strictly adhere to exploratory boundaries: no data was modified, no models were trained, no feature selection was executed, and no unverified semantic assumptions were made.

---

### 1. Dataset Overview
* **Source Filename:** `V1_dataset.csv`
* **Format:** Comma-Separated Values (CSV)
* **Dataset Scope:** Clinical and behavioral survey screening data for early-stage pulmonary disease detection.
* **Integrity Status:** Raw, unscaled, non-imputed, non-split.

---

### 2. Dataset Dimensions
* **Total Sample Count (Rows):** 3,000
* **Total Column Count:** 16
* **Input Feature Count:** 15 candidate predictor features
* **Target Columns:** 1 (`LUNG_CANCER`)
* **Memory Footprint:** 625.63 KB

---

### 3. Detected Feature List
The dataset columns were detected dynamically from the ingested CSV schema:
1. `GENDER`: Categorical ('M', 'F')
2. `AGE`: Continuous numerical (integer, years [30 - 80])
3. `SMOKING`: Discrete binary survey code ({1, 2})
4. `YELLOW_FINGERS`: Discrete binary survey code ({1, 2})
5. `ANXIETY`: Discrete binary survey code ({1, 2})
6. `PEER_PRESSURE`: Discrete binary survey code ({1, 2})
7. `CHRONIC_DISEASE`: Discrete binary survey code ({1, 2})
8. `FATIGUE`: Discrete binary survey code ({1, 2})
9. `ALLERGY`: Discrete binary survey code ({1, 2})
10. `WHEEZING`: Discrete binary survey code ({1, 2})
11. `ALCOHOL_CONSUMING`: Discrete binary survey code ({1, 2})
12. `COUGHING`: Discrete binary survey code ({1, 2})
13. `SHORTNESS_OF_BREATH`: Discrete binary survey code ({1, 2})
14. `SWALLOWING_DIFFICULTY`: Discrete binary survey code ({1, 2})
15. `CHEST_PAIN`: Discrete binary survey code ({1, 2})
16. `LUNG_CANCER`: Target label ('NO', 'YES')

---

### 4. Target Variable Analysis
* **Target Attribute:** `LUNG_CANCER`
* **Classification Formulation:** Supervised Binary Classification
* **Class Classes:** `['YES', 'NO']`
* **Class Frequencies:**
  * `YES`: 1,518 samples (50.60%)
  * `NO`:  1,482 samples (49.40%)
* **Imbalance Assessment:** Virtually balanced (imbalance ratio 1.024:1). This provides an optimal starting point for Parameterized Quantum Circuits (VQCs) and Quantum Support Vector Machines (QSVMs), avoiding majority-class gradient bias or the need for synthetic oversampling.

---

### 5. Missing-Value Analysis
* **Total Missing Values:** 0 across 48,000 data cells (0.00%).
* **Completeness Rate:** 100.00% complete data matrix.
* **Imputation Action:** Zero imputation required; verified clean data ingestion.

---

### 6. Duplicate Analysis
* **Exact Duplicate Rows:** 2 instances (0.0667% of dataset).
* **Identified Duplicate Pairs:**
  * Row index 962 and Row index 1476 (identical survey profile, `LUNG_CANCER = NO`)
  * Row index 1051 and Row index 2039 (identical survey profile, `LUNG_CANCER = YES`)
* **Actionable Preprocessing Recommendation:** Report documented. Exact duplicates should be resolved (e.g. deduplicated) prior to train/test partitioning to prevent cross-split leakage.

---

### 7. Numerical Analysis (`AGE`)
* **Feature:** `AGE`
* **Count:** 3,000
* **Mean:** 55.17 years
* **Median:** 55.00 years
* **Standard Deviation:** 14.72 years
* **Minimum:** 30.0 years
* **Maximum:** 80.0 years
* **Quartiles:** Q1 = 42.0, Q2 = 55.0, Q3 = 68.0, IQR = 26.0
* **Skewness:** 0.0033 (symmetric distribution across adult screening population)
* **Outlier Audit:** 0 outliers detected outside Tukey's bounds ([3.0, 107.0]).

---

### 8. Categorical & Discrete Feature Analysis
* All 13 survey variables exhibit balanced distributions across codes {1, 2} (roughly 49% to 51% each).
* `GENDER` distribution: {'M': 1514, 'F': 1486} (50.5% Male, 49.5% Female).
* **Semantic Objectivity Notice:** Integer encodings {1, 2} are preserved objectively as discrete nominal categories without speculative semantic assignments.

---

### 9. Constant & Low-Variance Analysis
* **Constant Features (Variance = 0):** None.
* **Near-Constant Features (>95% dominant class):** None.
* **Entropy Status:** High entropy across all candidate features, ensuring non-degenerate quantum parameter embeddings.

---

### 10. Invalid-Value Analysis
* **Biological Boundary Check:** All ages within biologically plausible range [30, 80].
* **Domain Check:** All binary features strictly adhere to {1, 2}; `GENDER` strictly adheres to {'M', 'F'}; target strictly adheres to {'NO', 'YES'}.
* **Token Integrity:** No hidden missing markers, sentinels (-999, '?'), or invalid whitespace detected.

---

### 11. Potential Leakage & Identifier Audit
* **High-Cardinality / ID Columns:** None detected.
* **Direct Target Proxies:** None detected (maximum correlation with target |r| < 0.20).
* **Post-Diagnostic Interventions:** None detected; all features reflect pre-diagnostic clinical and behavioral risk factors.

---

### 12. Feature Relationships (Inter-Feature Association)
* **Collinearity Analysis:** Maximum pairwise inter-feature Spearman correlation is modest (|r| < 0.10).
* **Circuit Implication:** Absence of extreme collinearity ensures that distinct qubits in the VQC will encode complementary information rather than redundant feature projections.
* **Epistemological Guardrail:** Inter-feature associations do not indicate causal interactions.

---

### 13. Exploratory Feature vs. Target Analysis
* **AGE vs. LUNG_CANCER:**
  * Cohort YES Mean: 54.65 years | Cohort NO Mean: 55.70 years
  * Welch's t-test p-value: 0.0504 | Mann-Whitney U test p-value: 0.0509
  * Status: Distribution difference noted; flagged as an exploratory predictive candidate.
* **Discrete Features vs. LUNG_CANCER:**
  * Features such as `WHEEZING`, `COUGHING`, `ALCOHOL_CONSUMING`, and `PEER_PRESSURE` exhibit slight exploratory distribution differences (p-values between 0.03 and 0.20).
  * Status: All 15 features remain candidate predictors for formal feature selection in subsequent stages.

---

### 14. Dataset Quality Matrix
* **Total Samples:** 3,000 (High statistical power)
* **Candidate Features:** 15 (Diverse screening factors)
* **Missing Values:** 0 (100% complete)
* **Exact Duplicates:** 2 (0.067%, actionable)
* **Schema Integrity:** 100% valid domains
* **Balance:** Balanced (50.6% / 49.4%)

---

### 15. Dataset Suitability for Hybrid Quantum Machine Learning (HQML)
The dataset satisfies all prerequisite technical criteria for the planned pipeline:
1. **Preprocessing Feasibility:** Clean baseline schema allows direct categorical encoding (e.g. standardizing to 0/1 or quantum phase angles in [0, pi]).
2. **Train/Validation/Test Partitioning:** 3,000 samples provide ample statistical support for a 70/15/15 or 80/10/10 stratified split without thinning minority support.
3. **Candidate Pool for Quantum Variational Circuits (VQC):**
   * **4-Feature VQC:** 15 candidate predictors available (requires 4 qubits, 16-dimensional Hilbert space).
   * **6-Feature VQC:** 15 candidate predictors available (requires 6 qubits, 64-dimensional Hilbert space).
   * **8-Feature VQC:** 15 candidate predictors available (requires 8 qubits, 256-dimensional Hilbert space).
   * The feature pool is fully sufficient to explore 4, 6, and 8 qubit configurations.

---

### 16. Limitations
1. **Lack of Metadata Dictionary:** Survey codes {1, 2} lack official author annotations regarding semantic orientation.
2. **Self-Reported Survey Nature:** Behavioral survey variables may carry subjective response variance.
3. **Absence of Longitudinal Clinical Biomarkers:** Data represents cross-sectional screening questionnaires without imaging (CT) or genomic markers.

---

### 17. Recommended Preprocessing Actions (Next Stage)
1. **Deduplication:** Remove the 2 identified redundant duplicate instances to ensure strict data partitioning hygiene.
2. **Encoding Standardization:** Standardize binary survey features from {1, 2} to {0, 1} and `GENDER` from {'M', 'F'} to {0, 1}.
3. **Continuous Feature Scaling:** Apply Min-Max scaling or Z-score standardization to `AGE` for classical models, or scale to $[0, \pi]$ for quantum angle embedding.
4. **Stratified Splitting:** Apply stratified partitioning (e.g. 70% Train, 15% Validation, 15% Test) using fixed random seeds.
5. **Feature Selection Execution:** Apply formal feature selection algorithms (e.g., Mutual Information, Recursive Feature Elimination, or Random Forest feature importance) to isolate optimal 4, 6, and 8 feature subsets for VQC and Classical SVM benchmarking.
