# Biomedical Dataset Preprocessing Report
**Run ID:** `26315dff-41c7-4e2a-bfdd-402b91d0a85d`  
**Dataset Source:** `C:\Users\logit\Downloads\hybrid-qml-disease-detection\ai_preprocessing_agent\data\input\lung_cancer.csv`  
**Status:** `SUCCESS`  
**Execution Time:** `1.25s`  

---

## 1. Dataset Overview
- **Total Rows Ingested:** 3000
- **Total Columns:** 16
- **Detected Target Column:** `LUNG_CANCER`
- **Identified Task Type:** `classification`
- **Numerical Features:** 1
- **Categorical Features:** 15

## 2. Data Quality
- **Duplicate Rows Detected:** 2
- **Missing Values Detected:** 0
- **Class Imbalance:** No

## 3. Problems Detected
- **[INFO] duplicates:** Found 2 exact duplicate rows (0.1%). (Recommended: *Remove duplicate rows to prevent bias and train/test leakage.*)

## 4. Preprocessing Plan
- **Plan Summary:** 3000 rows, 16 columns. Target: 'LUNG_CANCER' (classification).
- **Planned Steps:**
  1. **Remove Duplicates** (remove_duplicates): Eliminates identical duplicate rows to prevent statistical bias and partition contamination.
  2. **Stratified Dataset Split** (split_dataset): Partitions data into Train (70%), Val (15%), and Test (15%) with stratification to isolate evaluation distributions.
  3. **One-Hot Categorical Encoding** (encode_categorical_features): Encodes non-ordinal survey features into numeric dummy indicators fitted strictly on training data.
  4. **MinMax Feature Scaling** (scale_numerical_features): Scales continuous and indicator features into [0, 1] range required for quantum angle rotation embedding.
  5. **Quantum-Aligned Feature Selection** (select_features): Selects top 4 features via Mutual Information for non-linear correlation and compatibility with future 4-qubit VQC.

## 5. Operations Executed
- **Step 1 - Remove Duplicates:** Status: `success` | Columns: 16 -> 16 | Rows: 3000 -> 2998
- **Step 2 - Clean Categorical Casing:** Status: `success` | Columns: 16 -> 16 | Rows: 2998 -> 2998
- **Step 3 - Stratified Dataset Split:** Status: `success` | Columns: 16 -> 15 | Rows: 2998 -> 2098
- **Step 4 - Handle Missing Values:** Status: `success` | Columns: 15 -> 15 | Rows: 2098 -> 2098
- **Step 5 - Handle Outliers:** Status: `success` | Columns: 15 -> 15 | Rows: 2098 -> 2098
- **Step 6 - Encode Categorical Features:** Status: `success` | Columns: 1 -> 16 | Rows: 2098 -> 2098
- **Step 7 - Scale Numerical Features:** Status: `success` | Columns: 16 -> 16 | Rows: 2098 -> 2098

## 6. Feature Engineering
- **Applied:** No
- **Rationale:** No feature engineering applied (disabled by configuration).
- **New Features Generated:** []

## 7. Feature Selection
- **Selection Method:** `mutual_info`
- **Input Dimension:** 16 features
- **Selected Dimension:** 4 features
- **Selected Features:** `['ALCOHOL_CONSUMING', 'PEER_PRESSURE', 'SWALLOWING_DIFFICULTY', 'FATIGUE']`

## 8. Dimensionality Reduction
- **Applied:** No
- **Method:** `None`
- **Total Explained Variance:** `N/A`

## 9. Dataset Splitting
- **Split Strategy:** Stratified Train/Val/Test (Leakage Free)
- **Train Partition:** 2098 samples (70% if split else '70%')
- **Validation Partition:** 450 samples (15% if split else '15%')
- **Test Partition:** 450 samples (15% if split else '15%')
- **Random Seed:** `42`

## 10. Leakage Checks
- **Data Leakage Detected:** NO (Verified Clean)
- **Fit Isolation:** All imputation, encoding, scaling, and feature selection fitted strictly on `X_train`.
- **Validation & Test:** Strictly transformed without accessing evaluation distribution.

## 11. Validation
- **Overall Status:** `PASSED`
- **Checks Passed:** 6 / 6

## 12. Final Dataset
- **Train Matrix Shape:** `[2098, 4]`
- **Validation Matrix Shape:** `[450, 4]`
- **Test Matrix Shape:** `[450, 4]`

## 13. Selected Features
| Rank | Feature Name | Normalized Score | Selected |
| :--- | :--- | :--- | :--- |
| 1 | `ALCOHOL_CONSUMING` | 1.0000 | **YES** |
| 2 | `PEER_PRESSURE` | 0.5525 | **YES** |
| 3 | `SWALLOWING_DIFFICULTY` | 0.4920 | **YES** |
| 4 | `FATIGUE` | 0.4356 | **YES** |
| 5 | `GENDER_M` | 0.3718 | **NO** |
| 6 | `CHRONIC_DISEASE` | 0.1856 | **NO** |
| 7 | `SMOKING` | 0.1697 | **NO** |
| 8 | `SHORTNESS_OF_BREATH` | 0.1134 | **NO** |
| 9 | `ALLERGY` | 0.0746 | **NO** |
| 10 | `AGE` | 0.0000 | **NO** |
| 11 | `YELLOW_FINGERS` | 0.0000 | **NO** |
| 12 | `ANXIETY` | 0.0000 | **NO** |
| 13 | `WHEEZING` | 0.0000 | **NO** |
| 14 | `COUGHING` | 0.0000 | **NO** |
| 15 | `CHEST_PAIN` | 0.0000 | **NO** |
| 16 | `GENDER_F` | 0.0000 | **NO** |

## 14. Warnings
- ⚠️ Found 59124 identical feature rows between train and test (common in discrete survey data).

## 15. Reproducibility Information
- **Random State:** `42`
- **Python Version:** `3.12.8`
- **Scikit-Learn:** `1.9.1`
- **Pandas:** `3.0.6`
- **NumPy:** `2.5.3`

---
*Report generated deterministically by AI Preprocessing Agent.*