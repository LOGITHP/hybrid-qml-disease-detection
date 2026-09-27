"""Deterministic dataset analysis and profiling tool."""

import re
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd

from ..schemas.dataset import ColumnProfile, CandidateTarget, DatasetAnalysis


TARGET_KEYWORDS = [
    "target", "label", "class", "outcome", "diagnosis", "disease",
    "cancer", "status", "result", "condition", "lung_cancer"
]

ID_KEYWORDS = ["id", "identifier", "uuid", "guid", "patient_id", "subject_id", "index"]


def detect_inferred_type(series: pd.Series, col_name: str) -> str:
    """Infers semantic data type for a series."""
    clean_name = col_name.lower().strip()
    n_unique = series.nunique(dropna=True)
    n_total = len(series)

    # Check for identifier
    if any(k == clean_name or clean_name.endswith(f"_{k}") or clean_name.startswith(f"{k}_") for k in ID_KEYWORDS):
        if n_unique > n_total * 0.9:
            return "identifier"

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_numeric_dtype(series):
        # If numeric but low cardinality (e.g. 1/2 or 0/1/2 survey responses)
        if n_unique <= 5 and n_total > 20:
            return "categorical"
        return "numerical"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # String/object types
    if n_unique <= 20:
        return "categorical"
    if n_unique > n_total * 0.95:
        return "identifier"

    return "categorical"


def rank_target_candidates(df: pd.DataFrame, target_hint: Optional[str] = None) -> List[CandidateTarget]:
    """Ranks potential target columns based on naming, position, and cardinality."""
    candidates: List[CandidateTarget] = []

    for col in df.columns:
        clean_name = str(col).lower().strip()
        series = df[col].dropna()
        n_unique = series.nunique()
        n_total = len(series)

        if n_unique < 2 or n_unique > n_total * 0.5:
            continue  # Constants or high-cardinality IDs are unlikely targets

        confidence = 0.0
        rationale_parts = []

        # User hint matches
        if target_hint and clean_name == target_hint.lower().strip():
            confidence += 0.95
            rationale_parts.append(f"Explicitly matches configured target hint '{target_hint}'.")
        else:
            # Semantic keyword matches
            for kw in TARGET_KEYWORDS:
                if kw == clean_name:
                    confidence += 0.60
                    rationale_parts.append(f"Column name exactly matches target keyword '{kw}'.")
                    break
                elif kw in clean_name:
                    confidence += 0.40
                    rationale_parts.append(f"Column name contains target keyword '{kw}'.")
                    break

            # Position heuristic (often the last column in biomedical tabular data)
            if col == df.columns[-1]:
                confidence += 0.25
                rationale_parts.append("Located at the final column index.")

            # Cardinality heuristic (binary is classic classification target)
            if n_unique == 2:
                confidence += 0.20
                rationale_parts.append("Binary cardinality (2 distinct values).")
            elif 3 <= n_unique <= 10:
                confidence += 0.10
                rationale_parts.append(f"Multiclass cardinality ({n_unique} distinct values).")

        confidence = min(round(confidence, 2), 1.0)
        if confidence >= 0.30 or (target_hint and clean_name == target_hint.lower().strip()):
            # Infer task type
            if n_unique == 2:
                task_type = "binary_classification"
            elif 3 <= n_unique <= 20:
                task_type = "multiclass_classification"
            else:
                task_type = "regression"

            class_counts = series.value_counts().head(10).to_dict()
            candidates.append(CandidateTarget(
                column_name=str(col),
                confidence=confidence,
                task_type=task_type,
                rationale=" ".join(rationale_parts) or "Statistical target profile.",
                classes=[str(c) for c in series.unique()[:10]],
                class_counts={str(k): int(v) for k, v in class_counts.items()}
            ))

    # Sort descending by confidence
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    return candidates


def analyze_dataset(df: pd.DataFrame, target_hint: Optional[str] = None) -> DatasetAnalysis:
    """Performs comprehensive deterministic profiling of the dataset.

    Args:
        df: Input DataFrame
        target_hint: Optional column name specified by user or configuration

    Returns:
        DatasetAnalysis schema model
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    col_names = [str(c) for c in df.columns]

    numerical_features: List[str] = []
    categorical_features: List[str] = []
    boolean_features: List[str] = []
    identifier_columns: List[str] = []
    constant_columns: List[str] = []
    near_constant_columns: List[str] = []
    missing_dict: Dict[str, int] = {}
    profiles: Dict[str, ColumnProfile] = {}

    duplicate_rows = int(df.duplicated().sum())

    for col in df.columns:
        col_str = str(col)
        series = df[col]
        missing_count = int(series.isnull().sum())
        missing_ratio = float(missing_count / total_rows) if total_rows > 0 else 0.0
        if missing_count > 0:
            missing_dict[col_str] = missing_count

        unique_count = int(series.nunique(dropna=True))
        unique_ratio = float(unique_count / total_rows) if total_rows > 0 else 0.0

        inferred = detect_inferred_type(series, col_str)

        # Categorize column
        if unique_count <= 1:
            constant_columns.append(col_str)
        elif total_rows > 20 and (series.value_counts(normalize=True).iloc[0] if unique_count > 0 else 0) > 0.98:
            near_constant_columns.append(col_str)

        if inferred == "numerical":
            numerical_features.append(col_str)
        elif inferred == "categorical":
            categorical_features.append(col_str)
        elif inferred == "boolean":
            boolean_features.append(col_str)
        elif inferred == "identifier":
            identifier_columns.append(col_str)

        # Compute sample statistics
        stats: Dict[str, Any] = {}
        sample_vals = [str(v) for v in series.dropna().unique()[:5]]

        if pd.api.types.is_numeric_dtype(series) and inferred == "numerical":
            desc = series.describe()
            stats = {
                "min": float(desc.get("min", 0.0)),
                "max": float(desc.get("max", 0.0)),
                "mean": float(round(desc.get("mean", 0.0), 3)),
                "median": float(round(series.median(), 3)),
                "std": float(round(desc.get("std", 0.0), 3)),
            }
        else:
            mode_val = series.mode().iloc[0] if not series.mode().empty else None
            stats = {
                "mode": str(mode_val) if mode_val is not None else None,
                "top_frequencies": {str(k): int(v) for k, v in series.value_counts().head(5).items()}
            }

        profiles[col_str] = ColumnProfile(
            name=col_str,
            dtype=str(series.dtype),
            inferred_type=inferred,
            total_count=total_rows,
            missing_count=missing_count,
            missing_ratio=round(missing_ratio, 4),
            unique_count=unique_count,
            unique_ratio=round(unique_ratio, 4),
            sample_values=sample_vals,
            stats=stats
        )

    candidate_targets = rank_target_candidates(df, target_hint=target_hint)
    detected_target = candidate_targets[0].column_name if candidate_targets else None
    detected_task = candidate_targets[0].task_type if candidate_targets else None

    return DatasetAnalysis(
        row_count=total_rows,
        column_count=total_cols,
        column_names=col_names,
        numerical_features=numerical_features,
        categorical_features=categorical_features,
        boolean_features=boolean_features,
        identifier_columns=identifier_columns,
        constant_columns=constant_columns,
        near_constant_columns=near_constant_columns,
        missing_values=missing_dict,
        duplicate_rows=duplicate_rows,
        columns_profile=profiles,
        candidate_targets=candidate_targets,
        detected_target=detected_target,
        detected_task=detected_task
    )
