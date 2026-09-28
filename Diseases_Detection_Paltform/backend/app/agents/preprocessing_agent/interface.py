"""AI Preprocessing Agent interface orchestrating Gemma reasoning and deterministic sklearn pipelines."""

from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler, OneHotEncoder, OrdinalEncoder, RobustScaler, StandardScaler
from app.core.exceptions import ValidationError
from app.interfaces.preprocessing import IPreprocessingEngine
from app.llm.factory import LLMFactory
from app.schemas.preprocessing import PreprocessingPlan, PreprocessingPlanStep


def _stringify_non_missing(values: Any) -> np.ndarray:
    """Normalize mixed CSV categorical values while preserving missing values."""
    result = np.asarray(values, dtype=object).copy()
    for index in np.ndindex(result.shape):
        value = result[index]
        result[index] = np.nan if pd.isna(value) else str(value)
    return result


class PreprocessingAgent(IPreprocessingEngine):
    """Production AI Preprocessing Agent combining LLM clinical reasoning with deterministic tooling."""

    def __init__(self, llm_provider=None):
        self.llm = llm_provider or LLMFactory.get_provider()

    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute privacy-preserving statistical metadata without exposing raw biomedical records."""
        num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if not pd.api.types.is_bool_dtype(df[c])]
        cat_cols = [c for c in df.columns if c not in num_cols]
        missing_stats = {col: int(df[col].isna().sum()) for col in df.columns}
        column_profiles: Dict[str, Dict[str, Any]] = {}
        for col in df.columns:
            values = df[col]
            stats: Dict[str, Any]
            if col in num_cols:
                clean = pd.to_numeric(values, errors="coerce").dropna()
                clean = clean[np.isfinite(clean.to_numpy(dtype=float))]
                stats = clean.describe(percentiles=[0.25, 0.5, 0.75]).to_dict() if not clean.empty else {}
            else:
                stats = {
                    "unique_count": int(values.nunique(dropna=True)),
                    "top_frequencies": {str(k): int(v) for k, v in values.value_counts(dropna=True).head(10).items()},
                }
            column_profiles[str(col)] = {
                "dtype": str(values.dtype),
                "missing_count": missing_stats[col],
                "unique_count": int(values.nunique(dropna=True)),
                "statistics": {str(k): (float(v) if pd.notna(v) else None) for k, v in stats.items()},
                "sample_values": [str(v) for v in values.dropna().unique()[:5]],
            }

        return {
            "num_rows": int(len(df)),
            "num_columns": int(len(df.columns)),
            "columns": [str(c) for c in df.columns],
            "dtypes": {str(c): str(df[c].dtype) for c in df.columns},
            "numerical_columns": num_cols,
            "categorical_columns": cat_cols,
            "missing_values": missing_stats,
            "has_missing": any(v > 0 for v in missing_stats.values()),
            "column_profiles": column_profiles,
            "duplicate_rows": int(df.duplicated().sum()),
        }

    async def generate_plan(self, df: pd.DataFrame, target_column: str) -> PreprocessingPlan:
        """Formulate a step-by-step transformation plan via Gemma LLM reasoning."""
        if target_column not in df.columns:
            raise ValidationError(f"Target column '{target_column}' not found in uploaded dataset.")
        if df[target_column].isna().any():
            raise ValidationError("The selected target column contains missing values; resolve them before preprocessing.")
        stats = self.analyze_dataset(df)
        numerical_columns = [c for c in stats["numerical_columns"] if c != target_column]
        categorical_columns = [c for c in stats["categorical_columns"] if c != target_column]
        class_counts = df[target_column].value_counts(dropna=True)
        if len(class_counts) < 2:
            raise ValidationError("The selected target column must contain at least two classes.")
        if len(class_counts) > max(20, int(len(df) * 0.5)):
            raise ValidationError("The selected target looks continuous or high-cardinality; choose a classification target column.")

        prompt = (
            f"Given the uploaded tabular biomedical dataset with {stats['num_rows']} rows and "
            f"{stats['num_columns']} columns, its column schema is {stats['dtypes']}. "
            f"Numerical feature columns are {numerical_columns}; categorical feature columns are {categorical_columns}. "
            f"The user-selected target is '{target_column}' with {len(class_counts)} distinct classes. "
            f"The most frequent class counts are { {str(k): int(v) for k, v in class_counts.head(20).items()} }. "
            f"Per-column missing counts are {stats['missing_values']}. "
            f"Propose a clinical data preprocessing strategy ensuring no data leakage."
        )
        llm_recommendation = await self.llm.generate_response(prompt, context=stats)

        # Keep the executable plan tied to the uploaded data's actual schema.
        steps = [
            PreprocessingPlanStep(
                step_id=1,
                tool_name="stratified_split",
                rationale="Partition this uploaded dataset before fitting any transformations; stratify when class counts allow it.",
                parameters={"train_ratio": 0.70, "val_ratio": 0.15, "test_ratio": 0.15, "random_state": 42},
                fit_on_train_only=False,
            ),
        ]
        if numerical_columns:
            steps.extend([
                PreprocessingPlanStep(
                    step_id=len(steps) + 1,
                    tool_name="median_imputer",
                    rationale="Impute numeric columns from training-partition medians only.",
                    parameters={"strategy": "median", "columns": numerical_columns},
                    fit_on_train_only=True,
                ),
                PreprocessingPlanStep(
                    step_id=len(steps) + 2,
                    tool_name="min_max_scaler",
                    rationale="Scale numeric columns using ranges learned from training rows only.",
                    parameters={"columns": numerical_columns, "feature_range": [0, 1]},
                    fit_on_train_only=True,
                ),
            ])
        if categorical_columns:
            steps.extend([
                PreprocessingPlanStep(
                    step_id=len(steps) + 1,
                    tool_name="most_frequent_imputer",
                    rationale="Fill missing categorical values using the training-partition mode.",
                    parameters={"columns": categorical_columns},
                    fit_on_train_only=True,
                ),
                PreprocessingPlanStep(
                    step_id=len(steps) + 2,
                    tool_name="one_hot_encoder",
                    rationale="Encode categorical values observed in this dataset and safely ignore unseen validation/test categories.",
                    parameters={"columns": categorical_columns},
                    fit_on_train_only=True,
                ),
            ])

        return PreprocessingPlan(
            dataset_id="dataset_ref",
            dataset_version_id="version_ref",
            steps=steps,
            summary=llm_recommendation,
            leakage_prevention_guarantee="Transformers are fit strictly on training split; validation and test splits are transformed without refitting.",
        )

    def execute_plan(
        self,
        df: pd.DataFrame,
        plan: PreprocessingPlan,
        target_column: str,
        feature_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute preprocessing deterministically with strict data leakage prevention."""
        if target_column not in df.columns:
            raise ValidationError(f"Target column '{target_column}' not found in dataframe.")
        if df[target_column].isna().any():
            raise ValidationError("The selected target column contains missing values; resolve them before preprocessing.")
        if len(df) < 6:
            raise ValidationError("At least six rows are required to create train, validation, and test partitions.")

        plan_steps = plan.steps or []
        step_by_name = {step.tool_name.lower(): step for step in plan_steps}
        split_step = step_by_name.get("stratified_split")
        split_params = split_step.parameters if split_step else {}
        train_ratio = float(split_params.get("train_ratio", 0.70))
        val_ratio = float(split_params.get("val_ratio", 0.15))
        test_ratio = float(split_params.get("test_ratio", 0.15))
        ratio_sum = train_ratio + val_ratio + test_ratio
        if min(train_ratio, val_ratio, test_ratio) <= 0 or not np.isclose(ratio_sum, 1.0):
            raise ValidationError("Train, validation, and test ratios must be positive and sum to 1.")
        random_state = int(split_params.get("random_state", 42))

        X = df.drop(columns=[target_column]).copy()
        X = X.replace([np.inf, -np.inf], np.nan)
        y = df[target_column].copy()
        if X.shape[1] == 0:
            raise ValidationError("The uploaded dataset has no feature columns after selecting the target.")
        if feature_columns is not None:
            invalid = [column for column in feature_columns if column not in X.columns]
            if invalid:
                raise ValidationError(f"Selected features are not present in the uploaded dataset: {', '.join(invalid)}.")
            if not feature_columns:
                raise ValidationError("Select at least one feature column before training.")

        def can_stratify(labels: pd.Series, size: int) -> bool:
            counts = labels.value_counts(dropna=False)
            return len(counts) > 1 and int(counts.min()) >= 2 and size >= len(counts) and (len(labels) - size) >= len(counts)

        holdout_size = max(2, int(round(len(df) * (val_ratio + test_ratio))))
        holdout_size = min(holdout_size, len(df) - 2)
        stratify_all = y if can_stratify(y, holdout_size) else None
        X_train_raw, X_holdout, y_train, y_holdout = train_test_split(
            X,
            y,
            test_size=holdout_size,
            random_state=random_state,
            stratify=stratify_all,
        )
        test_fraction = test_ratio / (val_ratio + test_ratio)
        test_size = max(1, min(len(X_holdout) - 1, int(round(len(X_holdout) * test_fraction))))
        stratify_holdout = y_holdout if can_stratify(y_holdout, test_size) else None
        X_val_raw, X_test_raw, y_val, y_test = train_test_split(
            X_holdout,
            y_holdout,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify_holdout,
        )

        # Outlier bounds are estimated from the training partition and only remove training rows.
        outlier_step = step_by_name.get("iqr_outlier_removal") or step_by_name.get("remove_outliers")
        removed_outlier_rows = 0
        if outlier_step is not None:
            params = outlier_step.parameters
            candidate_cols = params.get("columns", list(X_train_raw.select_dtypes(include=[np.number]).columns))
            candidate_cols = [c for c in candidate_cols if c in X_train_raw.columns and pd.api.types.is_numeric_dtype(X_train_raw[c])]
            factor = float(params.get("factor", 1.5))
            row_mask = pd.Series(True, index=X_train_raw.index)
            for col in candidate_cols:
                values = pd.to_numeric(X_train_raw[col], errors="coerce")
                q1, q3 = values.quantile([0.25, 0.75])
                spread = q3 - q1
                if pd.notna(spread) and spread > 0:
                    row_mask &= values.isna() | values.between(q1 - factor * spread, q3 + factor * spread)
            removed_outlier_rows = int((~row_mask).sum())
            X_train_raw = X_train_raw.loc[row_mask]
            y_train = y_train.loc[row_mask]
            if X_train_raw.empty:
                raise ValidationError("Outlier removal excluded every training row; reduce the IQR factor or choose different columns.")

        if feature_columns is not None:
            X_train_raw = X_train_raw[feature_columns]
            X_val_raw = X_val_raw[feature_columns]
            X_test_raw = X_test_raw[feature_columns]
            X = X[feature_columns]

        numeric_columns = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c]) and not pd.api.types.is_bool_dtype(X[c])]
        categorical_columns = [c for c in X.columns if c not in numeric_columns]

        def configured_columns(tool_name: str, fallback: List[str]) -> List[str]:
            step = step_by_name.get(tool_name)
            requested = step.parameters.get("columns") if step else None
            return [c for c in (requested if requested is not None else fallback) if c in fallback]

        numeric_imputer_step = next((
            step for step in plan_steps
            if step.tool_name.lower() in {"median_imputer", "mean_imputer", "numeric_imputer"}
        ), None)
        numeric_strategy = "median"
        if numeric_imputer_step is not None:
            numeric_strategy = str(numeric_imputer_step.parameters.get("strategy", {
                "median_imputer": "median", "mean_imputer": "mean", "numeric_imputer": "median"
            }.get(numeric_imputer_step.tool_name.lower(), "median")))
        if numeric_strategy not in {"median", "mean", "most_frequent", "constant"}:
            raise ValidationError(f"Unsupported numeric imputation strategy '{numeric_strategy}'.")

        encoded_columns = configured_columns("one_hot_encoder", [])
        ordinal_columns = configured_columns("ordinal_encoder", [])
        has_encoder_step = any(
            step.tool_name.lower() in {"one_hot_encoder", "ordinal_encoder"}
            for step in plan_steps
        )
        if not encoded_columns and not ordinal_columns and not has_encoder_step:
            encoded_columns = categorical_columns
        overlap = set(encoded_columns) & set(ordinal_columns)
        if overlap:
            raise ValidationError(f"Categorical columns cannot use two encoders: {', '.join(sorted(overlap))}.")
        unencoded = set(categorical_columns) - set(encoded_columns) - set(ordinal_columns)
        # Unselected categoricals are left out of the model matrix instead of being silently coerced.

        transformers = []
        requested_numeric = numeric_imputer_step.parameters.get("columns") if numeric_imputer_step else None
        numeric_to_process = [c for c in (requested_numeric or numeric_columns) if c in numeric_columns]
        if not numeric_to_process:
            numeric_to_process = numeric_columns
        scale_step = next(
            (step for step in plan_steps if step.tool_name.lower() in {"min_max_scaler", "standard_scaler", "robust_scaler", "normalizer"}),
            None,
        )
        scale_columns = configured_columns(scale_step.tool_name.lower(), numeric_to_process) if scale_step else []
        scaled_numeric = [c for c in numeric_to_process if c in scale_columns]
        plain_numeric = [c for c in numeric_to_process if c not in scaled_numeric]
        if scaled_numeric:
            numeric_steps = [("imputer", SimpleImputer(strategy=numeric_strategy, keep_empty_features=True))]
            scale_name = scale_step.tool_name.lower()
            scaler = {
                "min_max_scaler": MinMaxScaler(feature_range=tuple(scale_step.parameters.get("feature_range", [0, 1]))),
                "standard_scaler": StandardScaler(),
                "robust_scaler": RobustScaler(),
                "normalizer": MinMaxScaler(feature_range=(0, 1)),
            }[scale_name]
            numeric_steps.append(("scaler", scaler))
            transformers.append(("numeric_scaled", Pipeline(numeric_steps), scaled_numeric))
        if plain_numeric:
            transformers.append(("numeric", Pipeline([
                ("imputer", SimpleImputer(strategy=numeric_strategy, keep_empty_features=True)),
            ]), plain_numeric))

        categorical_imputer_step = step_by_name.get("categorical_imputer") or step_by_name.get("most_frequent_imputer")
        categorical_strategy = "most_frequent"
        if categorical_imputer_step is not None:
            categorical_strategy = str(categorical_imputer_step.parameters.get("strategy", "most_frequent"))
        if categorical_strategy not in {"most_frequent", "constant"}:
            raise ValidationError(f"Unsupported categorical imputation strategy '{categorical_strategy}'.")
        fill_value = categorical_imputer_step.parameters.get("fill_value", "__missing__") if categorical_imputer_step else "__missing__"
        for name, columns, encoder in (
            ("one_hot", encoded_columns, OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ("ordinal", ordinal_columns, OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
        ):
            if columns:
                transformers.append((name, Pipeline([
                    ("stringify", FunctionTransformer(_stringify_non_missing, feature_names_out="one-to-one")),
                    ("imputer", SimpleImputer(
                        strategy=categorical_strategy,
                        fill_value=fill_value if categorical_strategy == "constant" else None,
                        keep_empty_features=True,
                    )),
                    ("encoder", encoder),
                ]), columns))

        if not transformers:
            raise ValidationError("Choose at least one numeric or encoded categorical feature column.")
        preprocessor = ColumnTransformer(transformers, remainder="drop", verbose_feature_names_out=True)
        X_train = preprocessor.fit_transform(X_train_raw)
        X_val = preprocessor.transform(X_val_raw)
        X_test = preprocessor.transform(X_test_raw)
        feature_names = [str(name) for name in preprocessor.get_feature_names_out()]

        return {
            "X_train": np.asarray(X_train, dtype=float),
            "X_val": np.asarray(X_val, dtype=float),
            "X_test": np.asarray(X_test, dtype=float),
            "y_train": y_train.to_numpy(),
            "y_val": y_val.to_numpy(),
            "y_test": y_test.to_numpy(),
            "feature_names": feature_names,
            "source_feature_names": [c for _, _, cols in transformers for c in cols],
            "fitted_pipeline": {"preprocessor": preprocessor, "target_column": target_column},
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "test_samples": len(X_test),
            "outlier_rows_removed": removed_outlier_rows,
            "unencoded_categorical_columns": sorted(unencoded),
        }

    def validate_result(self, splits: Dict[str, Any]) -> bool:
        """Verify processed arrays contain finite values and consistent feature dimensions."""
        expected_width = None
        for split_key in ["X_train", "X_val", "X_test"]:
            arr = np.asarray(splits[split_key])
            if arr.ndim != 2 or not np.isfinite(arr).all():
                return False
            if expected_width is None:
                expected_width = arr.shape[1]
            elif arr.shape[1] != expected_width:
                return False
        return True
