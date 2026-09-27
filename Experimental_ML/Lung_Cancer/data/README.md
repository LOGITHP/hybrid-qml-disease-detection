# Data Architecture & Specifications: Lung Cancer Screening

**Project:** Hybrid Quantum Machine Learning Platform for Early Disease Detection  
**Module:** Experimental ML / Lung Cancer  
**Location:** `Experimental_ML/Lung_Cancer/data/`  

---

## 1. Directory Structure

```
data/
├── raw/
│   └── V1_dataset.csv                   # Raw survey records (3,000 cases, 16 columns)
├── processed/
│   ├── X_train.csv                      # Full 15-feature train partition (N=2,098)
│   ├── X_validation.csv                 # Full 15-feature validation partition (N=450)
│   ├── X_test.csv                       # Full 15-feature holdout test partition (N=450)
│   ├── y_train.csv                      # Ground truth labels for train split
│   ├── y_validation.csv                 # Ground truth labels for validation split
│   ├── y_test.csv                       # Ground truth labels for holdout test split
│   ├── scaler.pkl                       # Fitted MinMaxScaler object (fit strictly on X_train)
│   ├── preprocessing_config.json        # Reproducibility metadata and mapping definitions
│   ├── target_mapping.json              # Binary label encoding mapping ('NO': 0, 'YES': 1)
│   ├── feature_names.json               # Ordered list of all 15 clinical predictors
│   ├── X_train_4.csv, X_val_4.csv, X_test_4.csv   # 4-feature clinical subset
│   ├── X_train_6.csv, X_val_6.csv, X_test_6.csv   # 6-feature clinical subset
│   ├── X_train_8.csv, X_val_8.csv, X_test_8.csv   # 8-feature clinical subset
│   ├── selected_features.json           # 4-feature subset definitions
│   ├── selected_features_6.json         # 6-feature subset definitions
│   └── selected_features_8.json         # 8-feature subset definitions
└── README.md
```

---

## 2. Raw Dataset Specification (`data/raw/V1_dataset.csv`)

* **Total Samples:** 3,000 patient records (2 duplicate rows removed during pipeline cleaning $\to$ 2,998 unique cases).
* **Target Feature:** `LUNG_CANCER` (Categorical: `YES` / `NO`).
* **Raw Predictor Columns:**
  1. `GENDER`: Categorical (`M` / `F`)
  2. `AGE`: Continuous integer (range 21–87)
  3. `SMOKING`: Survey scale (1 = No / Low, 2 = Yes / High)
  4. `YELLOW_FINGERS`: Survey scale (1 = No, 2 = Yes)
  5. `ANXIETY`: Survey scale (1 = No, 2 = Yes)
  6. `PEER_PRESSURE`: Survey scale (1 = No, 2 = Yes)
  7. `CHRONIC_DISEASE`: Survey scale (1 = No, 2 = Yes)
  8. `FATIGUE`: Survey scale (1 = No, 2 = Yes)
  9. `ALLERGY`: Survey scale (1 = No, 2 = Yes)
  10. `WHEEZING`: Survey scale (1 = No, 2 = Yes)
  11. `ALCOHOL_CONSUMING`: Survey scale (1 = No, 2 = Yes)
  12. `COUGHING`: Survey scale (1 = No, 2 = Yes)
  13. `SHORTNESS_OF_BREATH`: Survey scale (1 = No, 2 = Yes)
  14. `SWALLOWING_DIFFICULTY`: Survey scale (1 = No, 2 = Yes)
  15. `CHEST_PAIN`: Survey scale (1 = No, 2 = Yes)

---

## 3. Data Preprocessing & Splitting Protocol

1. **Stratification & Split Ratios:**
   * Split proportions: **70% Train** ($N = 2,098$), **15% Validation** ($N = 450$), **15% Holdout Test** ($N = 450$).
   * Stratified across `LUNG_CANCER` classes using fixed seed `random_state = 42`.
2. **Leakage-Free Transformation:**
   * Numerical features (`AGE`) and binary features are scaled using `MinMaxScaler(feature_range=(0.0, 1.0))`.
   * **Crucial Rule:** The scaler was fitted solely on $X_{train}$ and subsequently used to transform $X_{val}$ and $X_{test}$, preventing out-of-sample data leakage.
3. **Categorical Encodings:**
   * `GENDER`: Binary mapped (`F` $\to 0$, `M` $\to 1$).
   * Survey Predictors: Remapped from $\{1, 2\} \to \{0, 1\}$.
   * Target (`LUNG_CANCER`): Binary mapped (`NO` $\to 0$, `YES` $\to 1$).

---

## 4. Quantum-Compatible Feature Subsets

Because Variational Quantum Circuits scale in Hilbert space dimensionality according to $2^N$ (where $N$ is the number of qubits), multi-stage feature selection was applied in `03_feature_engineering_selection.ipynb` using Mutual Information and Sequential Forward Selection (SFS):

* **4-Feature Set:**
  `['WHEEZING', 'YELLOW_FINGERS', 'AGE', 'SHORTNESS_OF_BREATH']`
* **6-Feature Set:**
  `['COUGHING', 'PEER_PRESSURE', 'AGE', 'YELLOW_FINGERS', 'SHORTNESS_OF_BREATH', 'CHEST_PAIN']`
* **8-Feature Set:**
  `['COUGHING', 'PEER_PRESSURE', 'AGE', 'ANXIETY', 'ALLERGY', 'SHORTNESS_OF_BREATH', 'CHEST_PAIN', 'CHRONIC_DISEASE']`

---

## 5. Ethical & Clinical Usage Disclaimer

This dataset represents de-identified observational survey data for experimental and algorithmic benchmarking within the Hybrid Quantum Machine Learning Platform for Early Disease Detection. It is **not** a certified medical diagnostic device and must not be used for direct clinical decision-making without institutional clinical trial validation.
