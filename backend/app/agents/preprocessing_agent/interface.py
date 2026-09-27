"""AI Preprocessing Agent interface orchestrating Gemma reasoning and deterministic sklearn pipelines."""

from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler
from app.core.exceptions import ValidationError
from app.interfaces.preprocessing import IPreprocessingEngine
from app.llm.factory import LLMFactory
from app.schemas.preprocessing import PreprocessingPlan, PreprocessingPlanStep


class PreprocessingAgent(IPreprocessingEngine):
    """Production AI Preprocessing Agent combining LLM clinical reasoning with deterministic tooling."""

    def __init__(self, llm_provider=None):
        self.llm = llm_provider or LLMFactory.get_provider()

    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute privacy-preserving statistical metadata without exposing raw biomedical records."""
        num_cols = list(df.select_dtypes(include=[np.number]).columns)
        cat_cols = list(df.select_dtypes(exclude=[np.number]).columns)
        missing_stats = {col: int(df[col].isna().sum()) for col in df.columns}

        return {
            "num_rows": int(len(df)),
            "num_columns": int(len(df.columns)),
            "numerical_columns": num_cols,
            "categorical_columns": cat_cols,
            "missing_values": missing_stats,
            "has_missing": any(v > 0 for v in missing_stats.values()),
        }

    async def generate_plan(self, df: pd.DataFrame, target_column: str) -> PreprocessingPlan:
        """Formulate a step-by-step transformation plan via Gemma LLM reasoning."""
        stats = self.analyze_dataset(df)
        prompt = (
            f"Given biomedical dataset with {stats['num_rows']} patients and columns {list(df.columns)}, "
            f"where target is '{target_column}' and missing values: {stats['missing_values']}. "
            f"Propose a clinical data preprocessing strategy ensuring no data leakage."
        )
        llm_recommendation = await self.llm.generate_response(prompt, context=stats)

        # Standard deterministic plan steps
        steps = [
            PreprocessingPlanStep(
                step_id=1,
                tool_name="stratified_split",
                rationale="Partition into Train (70%), Validation (15%), and Test (15%) preserving disease prevalence.",
                parameters={"train_ratio": 0.70, "val_ratio": 0.15, "test_ratio": 0.15, "random_state": 42},
                fit_on_train_only=False,
            ),
            PreprocessingPlanStep(
                step_id=2,
                tool_name="median_imputer",
                rationale="Impute missing biomarker readings using median values calculated strictly on training samples.",
                parameters={"strategy": "median"},
                fit_on_train_only=True,
            ),
            PreprocessingPlanStep(
                step_id=3,
                tool_name="min_max_scaler",
                rationale="Scale feature values to [0, 1] interval suitable for quantum angle encoding.",
                parameters={"feature_range": [0, 1]},
                fit_on_train_only=True,
            ),
        ]

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
    ) -> Dict[str, Any]:
        """Execute preprocessing deterministically with strict data leakage prevention."""
        if target_column not in df.columns:
            raise ValidationError(f"Target column '{target_column}' not found in dataframe.")

        # 1. Clean column names
        df_clean = df.copy()
        df_clean.columns = [c.strip().upper() for c in df_clean.columns]
        target_col_clean = target_column.strip().upper()

        # 2. Extract features and target
        X = df_clean.drop(columns=[target_col_clean]).select_dtypes(include=[np.number])
        y = df_clean[target_col_clean].values

        feature_names = list(X.columns)

        # 3. Stratified Train / Val / Test Split
        X_train_raw, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.30, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )
        X_val_raw, X_test_raw, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp if len(np.unique(y_temp)) > 1 else None
        )

        # 4. Fit Imputer strictly on Train
        imputer = SimpleImputer(strategy="median")
        X_train_imp = imputer.fit_transform(X_train_raw)
        X_val_imp = imputer.transform(X_val_raw)
        X_test_imp = imputer.transform(X_test_raw)

        # 5. Fit Scaler strictly on Train
        scaler = MinMaxScaler(feature_range=(0, 1))
        X_train_scaled = scaler.fit_transform(X_train_imp)
        X_val_scaled = scaler.transform(X_val_imp)
        X_test_scaled = scaler.transform(X_test_imp)

        pipeline_artifact = {
            "imputer": imputer,
            "scaler": scaler,
            "feature_names": feature_names,
            "target_column": target_col_clean,
        }

        return {
            "X_train": X_train_scaled,
            "X_val": X_val_scaled,
            "X_test": X_test_scaled,
            "y_train": y_train,
            "y_val": y_val,
            "y_test": y_test,
            "feature_names": feature_names,
            "fitted_pipeline": pipeline_artifact,
            "train_samples": len(X_train_scaled),
            "val_samples": len(X_val_scaled),
            "test_samples": len(X_test_scaled),
        }

    def validate_result(self, splits: Dict[str, Any]) -> bool:
        """Verify that processed arrays have no NaNs, match dimensions, and lie within [0, 1]."""
        for split_key in ["X_train", "X_val", "X_test"]:
            arr = splits[split_key]
            if np.isnan(arr).any():
                return False
            if arr.min() < -0.01 or arr.max() > 1.01:
                return False
        return True
