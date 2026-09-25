# Stage 02: Preprocessing and Dataset Splitting Report
## Project: Hybrid Quantum Machine Learning Platform for Early Disease Detection
**Application:** Lung Cancer Screening & Classification  
**Target Column:** `LUNG_CANCER`  
**Random State:** `42`  

---

### 1. Objective
Transform raw clinical survey data into a clean, reproducible, and strictly leakage-free dataset partitioned for training, validation, and test evaluation, formatted for downstream feature selection and Quantum Variational Classifier (VQC) architectures.

---

### 2. Raw Dataset Size
* **Total Ingested Observations:** 3,000 rows
* **Total Attributes:** 16 (15 candidate predictors + 1 target)
* **Raw Target Distribution:** {'YES': 1518, 'NO': 1482}

---

### 3. Duplicate Handling
* **Exact Duplicate Rows Identified:** 2 instances.
* **Resolution:** Removed exact duplicates to prevent cross-split train/test data leakage.
* **Post-Deduplication Sample Count:** 2,998 rows.

---

### 4. Invalid-Value Handling
* **Domain Audit:** Verified biological age range [30, 80] and survey integer domains {1, 2}.
* **Result:** Zero invalid, impossible, or corrupted entries detected.

---

### 5. Removed Identifier Columns
* **Identifier Audit:** Audited for artificial patient IDs or index columns.
* **Action:** None removed. All 15 features represent valid demographic, behavioral, or symptom predictors.

---

### 6. Missing-Value Strategy
* **Total Missing Cells:** 0 across all 2,998 rows and 15 features.
* **Strategy:** No missing-value imputation was required.

---

### 7. Target Encoding
* **Target Mapping:** `NO -> 0`, `YES -> 1`
* **Distribution Post-Encoding:** Class 0 (NO): 1,481 (49.40%), Class 1 (YES): 1,517 (50.60%)
* **Class Balance Status:** Virtually balanced (1.024:1 ratio).

---

### 8. Input Feature Encoding
* `GENDER`: Mapped `F -> 0`, `M -> 1`.
* `13 Survey Features`: Standardized from {1, 2} to {0, 1} via $(x - 1)$.
* `AGE`: Preserved continuous numeric, scaled in step 11.
* **Total Features Preserved:** 15 candidate predictors. Zero feature selection performed.

---

### 9. Train / Validation / Test Split
* **Split Allocation:** 70% Train, 15% Validation, 15% Test.
* **Sample Counts:**
  * Training: 2,098 samples (70.0%)
  * Validation: 450 samples (15.0%)
  * Test: 450 samples (15.0%)

---

### 10. Stratification
* **Method:** Target-stratified multi-split (`stratify=y`).
* **Fidelity:** Class 1 (YES) accounts for 50.62% of Train, 50.67% of Validation, and 50.44% of Test.

---

### 11. Scaling Method & Quantum Suitability
* **Scaler:** `MinMaxScaler(feature_range=(0.0, 1.0))`
* **Quantum Compatibility:** Scales all features into $[0, 1]$, enabling direct mapping to single-qubit Pauli rotation angles $\theta_j = x_j \cdot \pi \in [0, \pi]$. This prevents angle wrap-around and barren plateau saturation.
* **Fitted Target:** Fitted strictly on `X_train` only.

---

### 12. Data-Leakage Prevention
* Scaler learned bounds exclusively from `X_train`.
* `X_validation` and `X_test` transformed strictly using training statistics.
* Test set kept entirely isolated.

---

### 13. Final Feature Count
* **Usable Predictor Features:** 15 candidate features preserved.

---

### 14. Final Sample Counts
* **Train:** 2,098 | **Validation:** 450 | **Test:** 450 | **Total:** 2,998

---

### 15. Preprocessing Limitations
* Self-reported survey answers may contain subjective bias.
* Binary symptom encodings do not capture longitudinal severity progression.
