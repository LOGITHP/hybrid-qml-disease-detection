"""AI preprocessing planner combining configured LLM reasoning with deterministic sklearn pipelines."""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler, OneHotEncoder, OrdinalEncoder, RobustScaler, StandardScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, mutual_info_classif, f_classif, VarianceThreshold, RFE, SelectFromModel

from app.core.exceptions import AppException, ValidationError
from app.interfaces.preprocessing import IPreprocessingEngine
from app.llm.factory import LLMFactory
from app.schemas.preprocessing import PreprocessingPlan, PreprocessingPlanStep, AIModifyRequest, AIModifyResponse

try:
    from imblearn.over_sampling import SMOTE, RandomOverSampler
    from imblearn.pipeline import Pipeline as ImblearnPipeline
    HAS_IMBLEARN = True
except ImportError:
    HAS_IMBLEARN = False
    # Fallback to sklearn Pipeline if imblearn isn't available
    ImblearnPipeline = Pipeline


def _stringify_non_missing(values: Any) -> np.ndarray:
    """Normalize mixed CSV categorical values while preserving missing values."""
    result = np.asarray(values, dtype=object).copy()
    for index in np.ndindex(result.shape):
        value = result[index]
        result[index] = np.nan if pd.isna(value) else str(value)
    return result


class SplitManager:
    """Handles Train / Validation / Test separation to prevent leakage."""
    @staticmethod
    def create_splits(df: pd.DataFrame, target_column: str, params: Dict[str, Any]) -> Tuple:
        train_ratio = float(params.get("train_ratio", 0.70))
        val_ratio = float(params.get("val_ratio", 0.15))
        test_ratio = float(params.get("test_ratio", 0.15))
        random_state = int(params.get("random_state", 42))

        if len(df) < 6:
            raise ValidationError("At least 6 rows are required to create train, validation, and test partitions.")
        if any(ratio <= 0 for ratio in (train_ratio, val_ratio, test_ratio)) or not np.isclose(
            train_ratio + val_ratio + test_ratio, 1.0
        ):
            raise ValidationError("Train, validation, and test ratios must be positive and add up to 1.")

        X = df.drop(columns=[target_column]).copy()
        y = df[target_column].copy()

        def can_stratify(labels: pd.Series, size: int) -> bool:
            counts = labels.value_counts(dropna=False)
            return len(counts) > 1 and int(counts.min()) >= 2 and size >= len(counts) and (len(labels) - size) >= len(counts)

        holdout_size = max(2, int(round(len(df) * (val_ratio + test_ratio))))
        holdout_size = min(holdout_size, len(df) - 2)
        stratify_all = y if can_stratify(y, holdout_size) else None
        
        X_train, X_holdout, y_train, y_holdout = train_test_split(
            X, y, test_size=holdout_size, random_state=random_state, stratify=stratify_all
        )
        
        test_fraction = test_ratio / (val_ratio + test_ratio)
        test_size = max(1, min(len(X_holdout) - 1, int(round(len(X_holdout) * test_fraction))))
        stratify_holdout = y_holdout if can_stratify(y_holdout, test_size) else None
        
        X_val, X_test, y_val, y_test = train_test_split(
            X_holdout, y_holdout, test_size=test_size, random_state=random_state, stratify=stratify_holdout
        )
        return X_train, X_val, X_test, y_train, y_val, y_test


class ClassBalancer:
    """Applies class balancing strictly on the training partition."""
    @staticmethod
    def apply(X_train: pd.DataFrame, y_train: pd.Series, method: str, random_state: int = 42) -> Tuple[pd.DataFrame, pd.Series]:
        if not HAS_IMBLEARN:
            raise ValidationError("imbalanced-learn package is required for class balancing (SMOTE).")
        
        if method.lower() == "smote":
            sampler = SMOTE(random_state=random_state)
        elif method.lower() == "random_oversample":
            sampler = RandomOverSampler(random_state=random_state)
        else:
            raise ValidationError(f"Unknown class balancing method: {method}")
        
        X_resampled, y_resampled = sampler.fit_resample(X_train, y_train)
        return pd.DataFrame(X_resampled, columns=X_train.columns), pd.Series(y_resampled, name=y_train.name)


class DimensionalityReducer:
    @staticmethod
    def get_pca(params: Dict[str, Any]) -> PCA:
        n_components = params.get("n_components", 4)
        return PCA(n_components=n_components, random_state=params.get("random_state", 42))


class FeatureSelectorFactory:
    @staticmethod
    def get_selector(method: str, params: Dict[str, Any]) -> Any:
        method = method.lower()
        if method == "mutual_information":
            return SelectKBest(score_func=mutual_info_classif, k=params.get("k", 10))
        elif method == "anova":
            return SelectKBest(score_func=f_classif, k=params.get("k", 10))
        elif method == "variance_threshold":
            return VarianceThreshold(threshold=params.get("threshold", 0.0))
        else:
            raise ValidationError(f"Unsupported feature selection method: {method}")


class PreprocessingAgent(IPreprocessingEngine):
    """Schema-aware preprocessing planner with deterministic pipeline execution."""

    def __init__(self, llm_provider=None):
        self.llm = llm_provider or LLMFactory.get_provider()

    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute privacy-preserving statistical metadata."""
        num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if not pd.api.types.is_bool_dtype(df[c])]
        cat_cols = [c for c in df.columns if c not in num_cols]
        missing_stats = {col: int(df[col].isna().sum()) for col in df.columns}
        column_profiles = {}
        for col in df.columns:
            values = df[col]
            if col in num_cols:
                clean = pd.to_numeric(values, errors="coerce").dropna()
                clean = clean[np.isfinite(clean.to_numpy(dtype=float))]
                raw_stats = clean.describe(percentiles=[0.25, 0.5, 0.75]).to_dict() if not clean.empty else {}
                stats = {str(k): (float(v) if pd.notna(v) else None) for k, v in raw_stats.items()}
            else:
                stats = {
                    "unique_count": int(values.nunique(dropna=True)),
                }
            column_profiles[str(col)] = {
                "dtype": str(values.dtype),
                "missing_count": missing_stats[col],
                "unique_count": int(values.nunique(dropna=True)),
                "statistics": stats,
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
        }

    async def modify_pipeline(self, payload: AIModifyRequest, df: pd.DataFrame) -> AIModifyResponse:
        """Ask the live LLM to refine a plan, then validate it against this upload."""
        instruction = payload.user_instruction.strip()
        target_column = payload.current_pipeline.target_column
        if not instruction:
            raise ValidationError("Enter a suggestion before asking the LLM to update the plan.")
        if not target_column or target_column not in df.columns:
            raise ValidationError("The plan target must be a column in the selected dataset.")
        if payload.current_pipeline.dataset_version_id != payload.dataset_version_id:
            raise ValidationError("The plan belongs to a different dataset version. Rebuild the plan and try again.")

        profile = self.analyze_dataset(df)
        schema = [
            {
                "name": str(column),
                "dtype": profile["dtypes"][str(column)],
                "missing_count": profile["missing_values"][str(column)],
                "unique_count": profile["column_profiles"][str(column)]["unique_count"],
            }
            for column in df.columns
        ]
        prompt = (
            "You are refining a tabular clinical-data preprocessing plan. Use the user's suggestion and the current plan. "
            "The dataset schema is authoritative. Do not invent columns or include the target as a feature. "
            "Only use operations from this list: stratified_split, numeric_imputer, median_imputer, mean_imputer, "
            "standard_scaler, min_max_scaler, robust_scaler, categorical_imputer, most_frequent_imputer, "
            "one_hot_encoder, ordinal_encoder, iqr_outlier_removal, outlier_removal, smote, class_balancer, "
            "feature_selection, pca. Keep stratified_split first. Keep all learned transformations fitted on training rows only. "
            "Return only valid JSON with keys explanation, warnings, and updated_pipeline. updated_pipeline must contain "
            "summary and steps; each step must contain step_id, tool_name, rationale, parameters, and fit_on_train_only.\n\n"
            f"Target column: {target_column}\n"
            f"Dataset schema and missing-value counts: {json.dumps(schema, ensure_ascii=False)}\n"
            f"Current plan: {payload.current_pipeline.model_dump_json()}\n"
            f"User suggestion: {instruction}"
        )

        if hasattr(self.llm, "generate_response_with_status"):
            response_text, used_live_model = await self.llm.generate_response_with_status(prompt)
        else:
            if not await self.llm.health_check():
                used_live_model = False
                response_text = ""
            else:
                response_text = await self.llm.generate_response(prompt)
                used_live_model = True
        if not used_live_model:
            raise AppException(
                status_code=503,
                code="LLM_UNAVAILABLE",
                message="The LLM did not process this suggestion because the configured model is unavailable or took too long to respond. Your current plan is unchanged.",
            )

        try:
            response_json = self._parse_json_response(response_text)
            candidate = response_json.get("updated_pipeline") or response_json.get("plan") or response_json
            if not isinstance(candidate, dict) or not isinstance(candidate.get("steps"), list):
                raise ValueError("The model response did not include an updated steps list.")
            provider_name = getattr(self.llm, "provider_name", self.llm.__class__.__name__)
            updated_plan = PreprocessingPlan.model_validate({
                "dataset_id": payload.dataset_id,
                "dataset_version_id": payload.dataset_version_id,
                "target_column": target_column,
                "steps": candidate["steps"],
                "summary": candidate.get("summary") or response_json.get("explanation") or "LLM-refined preprocessing plan.",
                "leakage_prevention_guarantee": payload.current_pipeline.leakage_prevention_guarantee,
                "generation_method": "llm",
                "generation_provider": provider_name,
                "generation_note": f"Refined by {provider_name} from your suggestion using the uploaded dataset schema.",
            })
            self._validate_refined_plan(df, updated_plan, target_column)
        except (ValueError, TypeError, KeyError) as exc:
            raise ValidationError(
                "The LLM responded, but its proposed plan was not valid for this dataset. The previous plan is unchanged. Try a more specific suggestion.",
                details={"reason": str(exc)},
            ) from exc

        warnings = response_json.get("warnings", [])
        if not isinstance(warnings, list):
            warnings = [str(warnings)]
        return AIModifyResponse(
            status="valid",
            explanation=str(response_json.get("explanation") or "The LLM returned a valid plan update."),
            changes=[],
            updated_pipeline=updated_plan,
            warnings=[str(warning) for warning in warnings],
        )

    @staticmethod
    def _parse_json_response(response_text: str) -> Dict[str, Any]:
        cleaned = (response_text or "").strip()
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end < start:
            raise ValueError("No JSON object was returned.")
        parsed = json.loads(cleaned[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("The model response must be a JSON object.")
        return parsed

    @staticmethod
    def _validate_refined_plan(df: pd.DataFrame, plan: PreprocessingPlan, target_column: str) -> None:
        """Reject model-proposed operations and columns the executor cannot safely use."""
        allowed_tools = {
            "stratified_split", "numeric_imputer", "median_imputer", "mean_imputer",
            "standard_scaler", "min_max_scaler", "robust_scaler", "categorical_imputer",
            "most_frequent_imputer", "one_hot_encoder", "ordinal_encoder", "iqr_outlier_removal",
            "outlier_removal", "smote", "class_balancer", "feature_selection", "pca",
        }
        numeric_columns = [
            str(column) for column in df.select_dtypes(include=[np.number]).columns
            if column != target_column and not pd.api.types.is_bool_dtype(df[column])
        ]
        categorical_columns = [str(column) for column in df.columns if str(column) != target_column and str(column) not in numeric_columns]
        feature_columns = numeric_columns + categorical_columns
        groups = {
            "split": {"stratified_split"},
            "numeric_imputer": {"numeric_imputer", "median_imputer", "mean_imputer"},
            "numeric_scaler": {"standard_scaler", "min_max_scaler", "robust_scaler"},
            "categorical_imputer": {"categorical_imputer", "most_frequent_imputer"},
            "categorical_encoder": {"one_hot_encoder", "ordinal_encoder"},
            "outlier": {"iqr_outlier_removal", "outlier_removal"},
            "balancer": {"smote", "class_balancer"},
            "feature_selection": {"feature_selection"},
            "pca": {"pca"},
        }
        seen_groups = set()
        normalized_steps = []
        for index, step in enumerate(plan.steps):
            tool_name = step.tool_name.strip().lower()
            if tool_name not in allowed_tools:
                raise ValueError(f"Unsupported preprocessing operation: {step.tool_name}.")
            group_name = next((name for name, values in groups.items() if tool_name in values), tool_name)
            if group_name in seen_groups:
                raise ValueError(f"Only one operation from the {group_name.replace('_', ' ')} group can be used.")
            seen_groups.add(group_name)
            step.step_id = f"step_{index + 1}"
            step.tool_name = tool_name
            step.fit_on_train_only = tool_name != "stratified_split"

            if tool_name == "stratified_split":
                if index != 0:
                    raise ValueError("stratified_split must be the first plan step.")
                params = step.parameters
                ratios = [float(params.get(key, default)) for key, default in (("train_ratio", 0.70), ("val_ratio", 0.15), ("test_ratio", 0.15))]
                if any(ratio <= 0 for ratio in ratios) or not np.isclose(sum(ratios), 1.0):
                    raise ValueError("Train, validation, and test split ratios must be positive and add up to 1.")

            numeric_tools = {
                "numeric_imputer", "median_imputer", "mean_imputer", "standard_scaler", "min_max_scaler",
                "robust_scaler", "iqr_outlier_removal", "outlier_removal",
            }
            categorical_tools = {"categorical_imputer", "most_frequent_imputer", "one_hot_encoder", "ordinal_encoder"}
            expected_columns = numeric_columns if tool_name in numeric_tools else categorical_columns if tool_name in categorical_tools else feature_columns
            if "columns" in step.parameters:
                selected = step.parameters["columns"]
                if isinstance(selected, str):
                    selected = [selected]
                if not isinstance(selected, list):
                    raise ValueError(f"The columns parameter for {tool_name} must be a list.")
                invalid = sorted(set(str(column) for column in selected) - set(expected_columns))
                if invalid:
                    raise ValueError(f"Columns are incompatible with {tool_name}: {invalid}.")
                step.parameters["columns"] = [str(column) for column in selected]
            elif tool_name in numeric_tools or tool_name in categorical_tools:
                step.parameters["columns"] = expected_columns

            if tool_name in {"numeric_imputer", "median_imputer", "mean_imputer"}:
                strategy = step.parameters.get("strategy") or {"median_imputer": "median", "mean_imputer": "mean"}.get(tool_name, "median")
                if strategy not in {"mean", "median", "most_frequent", "constant"}:
                    raise ValueError(f"Unsupported numeric imputation strategy: {strategy}.")
                step.parameters["strategy"] = strategy
            if tool_name in {"categorical_imputer", "most_frequent_imputer"}:
                strategy = step.parameters.get("strategy", "most_frequent")
                if strategy not in {"most_frequent", "constant"}:
                    raise ValueError(f"Unsupported categorical imputation strategy: {strategy}.")
                step.parameters["strategy"] = strategy
            if tool_name in {"smote", "class_balancer"} and step.parameters.get("method", "smote") not in {"smote", "random_oversample"}:
                raise ValueError("Class balancing method must be smote or random_oversample.")
            if tool_name in {"iqr_outlier_removal", "outlier_removal"}:
                factor = float(step.parameters.get("factor", 1.5))
                if factor <= 0 or not np.isfinite(factor):
                    raise ValueError("The IQR outlier factor must be a finite number greater than 0.")
                step.parameters["factor"] = factor
            if tool_name == "feature_selection" and step.parameters.get("method", "mutual_information") not in {"mutual_information", "anova", "variance_threshold"}:
                raise ValueError("Unsupported feature selection method.")
            if tool_name == "pca":
                try:
                    components = int(step.parameters.get("n_components", 2))
                except (TypeError, ValueError) as exc:
                    raise ValueError("PCA n_components must be a positive integer.") from exc
                if components < 1:
                    raise ValueError("PCA n_components must be a positive integer.")
                step.parameters["n_components"] = components

        if not plan.steps or plan.steps[0].tool_name != "stratified_split":
            raise ValueError("The plan must begin with stratified_split to keep learned transformations training-only.")

    async def generate_plan(self, df: pd.DataFrame, target_column: str) -> PreprocessingPlan:
        """Build a deterministic plan from the uploaded dataframe's schema and target."""
        stats = self.analyze_dataset(df)
        numerical_columns = [c for c in stats["numerical_columns"] if c != target_column]
        categorical_columns = [c for c in stats["categorical_columns"] if c != target_column]
        
        steps = [
            PreprocessingPlanStep(
                step_id="split", tool_name="stratified_split",
                parameters={"train_ratio": 0.70, "val_ratio": 0.15, "test_ratio": 0.15, "random_state": 42},
                fit_on_train_only=False
            )
        ]
        
        if numerical_columns:
            steps.append(PreprocessingPlanStep(
                step_id="num_imp", tool_name="median_imputer",
                parameters={"strategy": "median", "columns": numerical_columns}
            ))
            steps.append(PreprocessingPlanStep(
                step_id="num_scale", tool_name="standard_scaler",
                parameters={"columns": numerical_columns}
            ))
        if categorical_columns:
            steps.append(PreprocessingPlanStep(
                step_id="cat_imp", tool_name="most_frequent_imputer",
                parameters={"columns": categorical_columns}
            ))
            steps.append(PreprocessingPlanStep(
                step_id="cat_enc", tool_name="one_hot_encoder",
                parameters={"columns": categorical_columns}
            ))

        return PreprocessingPlan(
            dataset_id="dataset_ref", dataset_version_id="version_ref", target_column=target_column,
            steps=steps,
            summary="Schema-based preprocessing plan generated from the uploaded dataset.",
            generation_method="rule_based",
            generation_note="Built from the uploaded columns and data types using deterministic rules. No LLM call was made.",
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
            raise ValidationError(f"Target column '{target_column}' not found.")
        if df[target_column].isna().any():
            raise ValidationError(
                f"Target column '{target_column}' contains missing labels. Remove or label those rows before preprocessing."
            )

        # Infinite feature values behave like missing values for preprocessing. They
        # are imputed only when the approved plan requests an imputer; otherwise the
        # finite-value audit below returns a clear error.
        working_df = df.copy()
        numeric_feature_columns = [
            column for column in working_df.columns
            if column != target_column
            and pd.api.types.is_numeric_dtype(working_df[column])
            and not pd.api.types.is_bool_dtype(working_df[column])
        ]
        for column in numeric_feature_columns:
            working_df[column] = pd.to_numeric(working_df[column], errors="coerce").replace(
                [np.inf, -np.inf], np.nan
            )

        steps = plan.steps
        step_by_name = {step.tool_name.lower(): step for step in steps}

        def find_step(*tool_names: str) -> Optional[PreprocessingPlanStep]:
            return next((step_by_name[name] for name in tool_names if name in step_by_name), None)

        def configured_columns(
            step: Optional[PreprocessingPlanStep],
            available: List[str],
            default_to_all: bool = True,
        ) -> List[str]:
            if step is None:
                return []
            raw_columns = step.parameters.get("columns")
            if raw_columns is None:
                requested = list(available) if default_to_all else []
            elif isinstance(raw_columns, str):
                requested = [raw_columns]
            elif isinstance(raw_columns, list):
                requested = [str(column) for column in raw_columns]
            else:
                raise ValidationError(f"The columns parameter for '{step.tool_name}' must be a list of column names.")
            unknown = sorted(set(requested) - set(available))
            if unknown:
                raise ValidationError(
                    f"Preprocessing step '{step.tool_name}' refers to columns that are not available as features: {unknown}."
                )
            selected = set(requested)
            return [column for column in available if column in selected]
        
        # 1. SPLIT FIRST
        split_step = find_step("stratified_split")
        split_params = split_step.parameters if split_step else {}
        X_train_raw, X_val_raw, X_test_raw, y_train, y_val, y_test = SplitManager.create_splits(
            working_df, target_column, split_params
        )

        original_features = list(X_train_raw.columns)

        # Remove outlier rows from the training partition only, before learned
        # imputers/scalers are fitted. Missing values remain in the partition for
        # the configured imputer to handle.
        outlier_step = find_step("iqr_outlier_removal", "outlier_removal")
        outlier_rows_removed = 0
        if outlier_step:
            outlier_columns = configured_columns(outlier_step, numeric_feature_columns)
            factor = float(outlier_step.parameters.get("factor", 1.5))
            if factor <= 0:
                raise ValidationError("The IQR outlier factor must be greater than 0.")
            keep_rows = pd.Series(True, index=X_train_raw.index)
            for column in outlier_columns:
                values = pd.to_numeric(X_train_raw[column], errors="coerce")
                finite_values = values[np.isfinite(values.to_numpy(dtype=float, na_value=np.nan))].dropna()
                if finite_values.empty:
                    continue
                q1 = float(finite_values.quantile(0.25))
                q3 = float(finite_values.quantile(0.75))
                spread = q3 - q1
                lower_bound = q1 - factor * spread
                upper_bound = q3 + factor * spread
                within_bounds = values.isna() | values.between(lower_bound, upper_bound)
                keep_rows &= within_bounds
            outlier_rows_removed = int((~keep_rows).sum())
            X_train_raw = X_train_raw.loc[keep_rows].copy()
            y_train = y_train.loc[keep_rows].copy()
            if X_train_raw.empty:
                raise ValidationError("IQR outlier removal removed every training row. Select fewer columns or a larger IQR factor.")

        # 2. COLUMN TRANSFORMER (Imputation, Scaling, Encoding)
        num_cols = [
            c for c in X_train_raw.columns
            if pd.api.types.is_numeric_dtype(X_train_raw[c]) and not pd.api.types.is_bool_dtype(X_train_raw[c])
        ]
        cat_cols = [c for c in X_train_raw.columns if c not in num_cols]
        
        transformers = []
        # Numeric operations are applied only to the columns named in the plan.
        # Grouping columns by operation keeps the saved transformer fit-on-train
        # while honoring the user's per-column scaling selection.
        num_imputer_step = find_step("numeric_imputer", "median_imputer", "mean_imputer")
        num_scale_step = find_step("standard_scaler", "min_max_scaler", "robust_scaler")
        impute_num_cols = configured_columns(num_imputer_step, num_cols)
        scale_num_cols = configured_columns(num_scale_step, num_cols)

        num_strategy = "median"
        if num_imputer_step:
            num_strategy = num_imputer_step.parameters.get("strategy") or {
                "mean_imputer": "mean",
                "median_imputer": "median",
            }.get(num_imputer_step.tool_name.lower(), "median")
            if num_strategy not in {"mean", "median", "most_frequent", "constant"}:
                raise ValidationError(f"Unsupported numeric imputation strategy: {num_strategy}.")
        num_fill_value = num_imputer_step.parameters.get("fill_value", 0) if num_imputer_step else 0

        scaler_name = num_scale_step.tool_name.lower() if num_scale_step else ""
        scaler_factory = {
            "standard_scaler": StandardScaler,
            "min_max_scaler": MinMaxScaler,
            "robust_scaler": RobustScaler,
        }.get(scaler_name)
        numeric_groups: Dict[Tuple[bool, bool], List[str]] = {}
        for column in num_cols:
            key = (column in impute_num_cols, column in scale_num_cols)
            numeric_groups.setdefault(key, []).append(column)
        for (should_impute, should_scale), columns in numeric_groups.items():
            num_pipe_steps = []
            if should_impute:
                num_pipe_steps.append((
                    "imputer",
                    SimpleImputer(strategy=num_strategy, fill_value=num_fill_value, keep_empty_features=True),
                ))
            if should_scale and scaler_factory:
                num_pipe_steps.append(("scaler", scaler_factory()))
            transformer: Any = Pipeline(num_pipe_steps) if num_pipe_steps else "passthrough"
            transformers.append((f"numeric_{len(transformers)}", transformer, columns))

        # A category is encoded only when it appears in the approved encoder step.
        # This is important for the UI's promise that unchecked categories are
        # omitted rather than silently included in the model matrix.
        cat_imputer_step = find_step("categorical_imputer", "most_frequent_imputer")
        cat_enc_step = find_step("one_hot_encoder", "ordinal_encoder")
        encoded_cat_cols = configured_columns(cat_enc_step, cat_cols) if cat_enc_step else []
        impute_cat_cols = configured_columns(cat_imputer_step, cat_cols) if cat_imputer_step else []
        unencoded_categorical_columns = [column for column in cat_cols if column not in encoded_cat_cols]

        if cat_enc_step and encoded_cat_cols:
            cat_strategy = cat_imputer_step.parameters.get("strategy", "most_frequent") if cat_imputer_step else "most_frequent"
            if cat_strategy not in {"most_frequent", "constant"}:
                raise ValidationError(f"Unsupported categorical imputation strategy: {cat_strategy}.")
            cat_fill_value = cat_imputer_step.parameters.get("fill_value", "__missing__") if cat_imputer_step else "__missing__"
            for should_impute in (True, False):
                columns = [column for column in encoded_cat_cols if (column in impute_cat_cols) == should_impute]
                if not columns:
                    continue
                cat_pipe_steps = [(
                    "stringify",
                    FunctionTransformer(_stringify_non_missing, feature_names_out="one-to-one"),
                )]
                if should_impute:
                    cat_pipe_steps.append((
                        "imputer",
                        SimpleImputer(strategy=cat_strategy, fill_value=cat_fill_value, keep_empty_features=True),
                    ))
                if cat_enc_step.tool_name.lower() == "one_hot_encoder":
                    cat_pipe_steps.append(("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)))
                else:
                    cat_pipe_steps.append((
                        "encoder",
                        OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
                    ))
                transformers.append((f"categorical_{len(transformers)}", Pipeline(cat_pipe_steps), columns))

        if not transformers:
            raise ValidationError("The selected preprocessing plan leaves no usable feature columns.")

        preprocessor = ColumnTransformer(transformers, remainder="drop")
        
        # Main execution pipeline
        X_train_t = preprocessor.fit_transform(X_train_raw)
        X_val_t = preprocessor.transform(X_val_raw)
        X_test_t = preprocessor.transform(X_test_raw)
        
        current_feature_names = preprocessor.get_feature_names_out()
        
        # DataFrame wrapper for selection
        X_train_df = pd.DataFrame(X_train_t, columns=current_feature_names, index=X_train_raw.index)
        X_val_df = pd.DataFrame(X_val_t, columns=current_feature_names, index=X_val_raw.index)
        X_test_df = pd.DataFrame(X_test_t, columns=current_feature_names, index=X_test_raw.index)

        if X_train_df.shape[1] == 0:
            raise ValidationError("The selected preprocessing plan leaves no usable feature columns.")

        # 3. CLASS BALANCING (ONLY ON TRAIN)
        balancer_step = find_step("smote", "class_balancer")
        if balancer_step:
            method = balancer_step.parameters.get("method", "smote")
            X_train_df, y_train = ClassBalancer.apply(X_train_df, y_train, method)

        # 4. FEATURE SELECTION
        fs_step = find_step("feature_selection")
        selected_features = None
        if fs_step:
            method = fs_step.parameters.get("method", "mutual_information")
            selector = FeatureSelectorFactory.get_selector(method, fs_step.parameters)
            selector.fit(X_train_df, y_train)
            support = selector.get_support()
            X_train_df = X_train_df.loc[:, support]
            X_val_df = X_val_df.loc[:, support]
            X_test_df = X_test_df.loc[:, support]
            selected_features = list(X_train_df.columns)

        # 5. PCA
        pca_step = find_step("pca")
        if pca_step:
            pca = DimensionalityReducer.get_pca(pca_step.parameters)
            if len(X_train_df.columns) < pca.n_components:
                raise ValidationError(f"Cannot apply PCA with {pca.n_components} components on {len(X_train_df.columns)} features.")
            
            X_train_pca = pca.fit_transform(X_train_df)
            X_val_pca = pca.transform(X_val_df)
            X_test_pca = pca.transform(X_test_df)
            
            pc_names = [f"PC{i+1}" for i in range(pca.n_components)]
            X_train_df = pd.DataFrame(X_train_pca, columns=pc_names, index=X_train_df.index)
            X_val_df = pd.DataFrame(X_val_pca, columns=pc_names, index=X_val_df.index)
            X_test_df = pd.DataFrame(X_test_pca, columns=pc_names, index=X_test_df.index)

        result = {
            "X_train": X_train_df.to_numpy(),
            "X_val": X_val_df.to_numpy(),
            "X_test": X_test_df.to_numpy(),
            "y_train": y_train.to_numpy(),
            "y_val": y_val.to_numpy(),
            "y_test": y_test.to_numpy(),
            "feature_names": list(X_train_df.columns),
            "original_features": original_features,
            "selected_features": selected_features,
            "fitted_pipeline": {"preprocessor": preprocessor, "target_column": target_column},
            "train_samples": len(X_train_df),
            "val_samples": len(X_val_df),
            "test_samples": len(X_test_df),
            "outlier_rows_removed": outlier_rows_removed,
            "unencoded_categorical_columns": unencoded_categorical_columns,
        }
        if not self.validate_result(result):
            raise ValidationError(
                "Preprocessing produced empty, non-finite, or inconsistent feature arrays. Review imputation and selected columns."
            )
        return result

    def validate_result(self, splits: Dict[str, Any]) -> bool:
        """Verify processed arrays contain finite values and consistent feature dimensions."""
        expected_width = None
        for split_key in ["X_train", "X_val", "X_test"]:
            arr = np.asarray(splits[split_key])
            try:
                finite = np.isfinite(arr).all()
            except TypeError:
                return False
            if arr.ndim != 2 or arr.shape[1] == 0 or not finite:
                return False
            if expected_width is None:
                expected_width = arr.shape[1]
            elif arr.shape[1] != expected_width:
                return False
        return True
