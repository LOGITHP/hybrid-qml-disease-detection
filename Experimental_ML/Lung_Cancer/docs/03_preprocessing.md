# 03. Data Preprocessing & Data Leakage Prevention Framework

## 1. Leakage Prevention Protocol
Data leakage occurs when information from the validation or test sets inadvertently influences training (e.g., fitting scalers on the full dataset or selecting features using all samples). To eliminate leakage, our pipeline enforces strict procedural isolation:

$$\text{Raw Data} \longrightarrow \text{Split Partitioning (Train/Val/Test)} \longrightarrow \text{Fit Scaler on Train Only} \longrightarrow \text{Transform Val/Test} \longrightarrow \text{Model Input}$$

## 2. Partitioning Strategy
The 2,998 records were partitioned using stratified sampling to guarantee identical class balance across sets:
- **Training Set**: 2,098 samples (70.0%) — exclusively used for parameter optimization and feature selection.
- **Validation Set**: 450 samples (15.0%) — used for hyperparameter cross-validation, SFS subset scoring, and epoch checkpointing.
- **Holdout Test Set**: 450 samples (15.0%) — kept completely isolated and evaluated only once per model.
  - Test set composition: 227 positive cases (`LUNG_CANCER=1`), 223 negative cases (`LUNG_CANCER=0`).
- **Random Seed**: Fixed to `42` for strict reproducibility.

## 3. Standardization & Transformation Details
1. **Binary Feature Mapping**:
   - `GENDER`: $\text{M} \to 1.0$, $\text{F} \to 0.0$.
   - Symptom responses (encoded as 1 and 2 in raw records) mapped linearly: $1 \to 0.0$ (Absent), $2 \to 1.0$ (Present).
   - Target variable `LUNG_CANCER`: $\text{YES} \to 1$, $\text{NO} \to 0$.
2. **Continuous Feature Scaling (Age)**:
   - Continuous `AGE` values scaled to $[0, 1]$ using scikit-learn `MinMaxScaler`:
     $$x_{\text{scaled}} = \frac{x - x_{\min}^{\text{train}}}{x_{\max}^{\text{train}} - x_{\min}^{\text{train}}}$$
   - The scaling parameters ($x_{\min} = 21, x_{\max} = 87$) were derived strictly from the training partition and saved to `data/processed/minmax_scaler.joblib`.
3. **Feature Space Normalization**:
   - Every input feature in the final matrices lies strictly in the interval $[0.0, 1.0]$. This is essential for quantum angle embedding, where each value maps directly to a rotational angle on the Bloch sphere ($x_i \cdot \pi \in [0, \pi]$).
