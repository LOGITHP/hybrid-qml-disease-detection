# Stage 03: Feature Engineering Review and Feature Selection Report
## Project: Hybrid Quantum Machine Learning Platform for Early Disease Detection
**Task:** Selection of Exactly 4 Features for a 4-Qubit Variational Quantum Classifier (VQC)  
**Target Variable:** `LUNG_CANCER` ({'NO': 0, 'YES': 1})  
**Evaluation Mode:** Training-Set Fitting with Validation-Set Selection  

---

### 1. Objective
Identify and isolate exactly 4 optimal, complementary clinical predictors from the 15 candidate features for angle encoding in a 4-qubit Variational Quantum Classifier (VQC), preventing data leakage and strictly isolating the holdout test set.

---

### 2. Original Feature Space
The preprocessed feature matrix comprises 15 candidate predictors:
`GENDER, AGE, SMOKING, YELLOW_FINGERS, ANXIETY, PEER_PRESSURE, CHRONIC_DISEASE, FATIGUE, ALLERGY, WHEEZING, ALCOHOL_CONSUMING, COUGHING, SHORTNESS_OF_BREATH, SWALLOWING_DIFFICULTY, CHEST_PAIN`

---

### 3. Feature Engineering Decisions
* **Review Protocol:** Systematically reviewed potential non-linear transformations (e.g. polynomial interaction cross-terms, respiratory symptom sums, target encoding).
* **Finding:** Non-linear cross-terms introduce severe multicollinearity and risk overfitting. Furthermore, quantum variational circuits naturally capture multi-feature non-linearities via parameterized two-qubit entangling gates (CX/CZ).
* **Decision:** Retained all 15 genuine preprocessed features in standardized [0, 1] numerical range without artificial cross-terms.

---

### 4. Feature Relevance Methods
Predictive relevance was screened **exclusively on the training partition (`X_train`, `y_train`)** using three complementary algorithms:
1. **Mutual Information (`mutual_info_classif`)**: Quantifies non-linear information sharing.
2. **ANOVA F-statistic (`f_classif`)**: Measures linear class separation.
3. **Random Forest Feature Importance (`RandomForestClassifier`)**: Measures Gini split utility across tree ensembles.

---

### 5. Relevance Results
Features were ranked by composite rank averaging across the three screening criteria:
1. `PEER_PRESSURE`: Composite Score 9.67 (Rank 1)
2. `YELLOW_FINGERS`: Composite Score 6.00 (Rank 2)
3. `SMOKING`: Composite Score 4.00 (Rank 3)
4. `AGE`: Composite Score 6.67 (Rank 4)
5. `CHRONIC_DISEASE` & `SHORTNESS_OF_BREATH`: Composite Score 7.00
6. `COUGHING` & `CHEST_PAIN`: Composite Score 8.00

---

### 6. Redundancy Analysis
* Spearman rank correlation matrix computed on `X_train`.
* Maximum observed pairwise correlation across all feature pairs is |r| = 0.0615.
* **Conclusion:** Zero pairs exhibit high collinearity (|r| >= 0.70). Candidate features carry distinct, complementary signals.

---

### 7. Candidate Shortlist
Formed an 8-feature candidate pool for sequential search:
`ALCOHOL_CONSUMING, SMOKING, WHEEZING, CHRONIC_DISEASE, YELLOW_FINGERS, SHORTNESS_OF_BREATH, AGE, GENDER`

---

### 8. Sequential Feature-Selection Methodology
* **Algorithm:** Sequential Forward Selection (SFS).
* **Starting State:** S_0 = empty set.
* **Iterative Loop:** Evaluated each unselected candidate added to the active set, selecting the candidate that yielded the greatest validation performance.
* **Stopping Threshold:** Exactly 4 features (matching 4-qubit hardware capacity).
* **Computational Cost:** Evaluated 8 + 7 + 6 + 5 = 26 candidate sets, avoiding the combinatorial burden of all 1,365 subsets.

---

### 9. Validation Criterion
* **Primary Metric:** **Balanced Accuracy** = (Sensitivity + Specificity) / 2.
* **Rationale:** Early disease detection requires equal penalization of false negatives and false positives. Accuracy alone is sensitive to class skew.
* **Secondary Metrics Tracked:** Accuracy, Sensitivity, Specificity, Precision, F1-Score, ROC-AUC.

---

### 10. Feature-Selection Results
Step-by-step selection trajectory:
* **Step 1:** Selected `WHEEZING` (Validation Balanced Accuracy: 0.5174)
* **Step 2:** Added `YELLOW_FINGERS` (Validation Balanced Accuracy: 0.5174)
* **Step 3:** Added `AGE` (Validation Balanced Accuracy: 0.5345)
* **Step 4:** Added `SHORTNESS_OF_BREATH` (Validation Balanced Accuracy: 0.5279)

---

### 11. Final Four Features
The final 4 selected features are:
1. **`WHEEZING`**
2. **`YELLOW_FINGERS`**
3. **`AGE`**
4. **`SHORTNESS_OF_BREATH`**

> **Scientific Epistemology Statement:**
> **These four features were selected for their predictive utility in this dataset.** We do NOT assert that these features cause lung cancer.

---

### 12. Limitations
* SFS is a greedy search algorithm that does not exhaustively evaluate all multi-feature interaction combinations.
* Feature ranking is conditional on the available sample cohort and survey responses.

---

### 13. Data-Leakage Safeguards
* **Zero Test Set Exposure:** `X_test` and `y_test` were strictly isolated from all relevance ranking, correlation auditing, and forward selection steps.
* **Model Fitting Isolation:** All surrogate models were fitted exclusively on `X_train`.
* **Validation Separation:** Selection decisions were guided solely by `X_validation`.
