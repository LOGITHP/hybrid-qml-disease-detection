"""Data quality analysis tools for biomedical dataset verification."""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from ..schemas.quality import QualityFinding, DataQualityReport


def detect_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
    """Detects missing value statistics per column."""
    missing_counts = df.isnull().sum()
    affected = {str(col): int(count) for col, count in missing_counts.items() if count > 0}
    total_missing = int(missing_counts.sum())
    return {
        "status": "success",
        "total_missing": total_missing,
        "affected_columns": list(affected.keys()),
        "missing_counts": affected,
        "has_missing": total_missing > 0
    }


def detect_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
    """Detects exact duplicate records."""
    dup_count = int(df.duplicated().sum())
    dup_ratio = float(dup_count / len(df)) if len(df) > 0 else 0.0
    return {
        "status": "success",
        "duplicate_count": dup_count,
        "duplicate_ratio": round(dup_ratio, 4),
        "has_duplicates": dup_count > 0
    }


def detect_invalid_values(df: pd.DataFrame) -> Dict[str, Any]:
    """Detects infinite numbers, empty strings, and null-equivalent tokens."""
    invalid_tokens = ["na", "null", "none", "?", "unknown", "nan", "inf", "-inf", ""]
    token_findings: Dict[str, int] = {}
    inf_findings: Dict[str, int] = {}

    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            num_infs = int(np.isinf(series).sum()) if series.notnull().any() else 0
            if num_infs > 0:
                inf_findings[str(col)] = num_infs
        else:
            str_series = series.astype(str).str.strip().str.lower()
            count = int(str_series.isin(invalid_tokens).sum())
            if count > 0:
                token_findings[str(col)] = count

    return {
        "status": "success",
        "infinite_values": inf_findings,
        "string_token_nulls": token_findings,
        "has_invalid_values": len(token_findings) > 0 or len(inf_findings) > 0
    }


def detect_inconsistent_categories(df: pd.DataFrame) -> Dict[str, Any]:
    """Detects case inconsistencies (e.g. 'YES', 'yes', 'Yes') in categorical columns."""
    inconsistent: Dict[str, List[str]] = {}
    for col in df.select_dtypes(include=["object", "string", "category"]).columns:
        vals = [str(x).strip() for x in df[col].dropna().unique()]
        lower_map: Dict[str, set] = {}
        for v in vals:
            lower_map.setdefault(v.lower(), set()).add(v)
        multi_case = [list(variants) for variants in lower_map.values() if len(variants) > 1]
        if multi_case:
            inconsistent[str(col)] = [item for sublist in multi_case for item in sublist]

    return {
        "status": "success",
        "inconsistent_columns": inconsistent,
        "has_inconsistencies": len(inconsistent) > 0
    }


def detect_outliers(df: pd.DataFrame) -> Dict[str, Any]:
    """Detects statistical outliers using IQR rule on continuous numerical features."""
    outlier_counts: Dict[str, int] = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        if series.nunique() <= 5:
            continue  # Skip discrete/survey encoded features
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            n_outliers = int(((series < lower) | (series > upper)).sum())
            if n_outliers > 0:
                outlier_counts[str(col)] = n_outliers

    return {
        "status": "success",
        "outlier_counts": outlier_counts,
        "has_outliers": len(outlier_counts) > 0
    }


def detect_constant_features(df: pd.DataFrame) -> Dict[str, Any]:
    """Detects completely constant columns (0 variance)."""
    constants = [str(c) for c in df.columns if df[c].nunique(dropna=False) <= 1]
    return {
        "status": "success",
        "constant_columns": constants,
        "has_constants": len(constants) > 0
    }


def detect_near_constant_features(df: pd.DataFrame, threshold: float = 0.98) -> Dict[str, Any]:
    """Detects columns where a single value comprises > threshold of entries."""
    near_constants = []
    for c in df.columns:
        if df[c].nunique() > 1:
            top_freq = df[c].value_counts(normalize=True).iloc[0]
            if top_freq >= threshold:
                near_constants.append(str(c))
    return {
        "status": "success",
        "near_constant_columns": near_constants,
        "has_near_constants": len(near_constants) > 0
    }


def detect_high_correlations(df: pd.DataFrame, threshold: float = 0.90) -> List[Dict[str, Any]]:
    """Detects collinear pairs among numerical features."""
    num_cols = df.select_dtypes(include=[np.number]).columns
    if len(num_cols) < 2:
        return []

    corr_matrix = df[num_cols].corr().abs()
    high_pairs = []
    for i in range(len(num_cols)):
        for j in range(i + 1, len(num_cols)):
            col1 = num_cols[i]
            col2 = num_cols[j]
            score = corr_matrix.loc[col1, col2]
            if score >= threshold:
                high_pairs.append({
                    "feature_1": str(col1),
                    "feature_2": str(col2),
                    "correlation": float(round(score, 4))
                })
    return high_pairs


def detect_class_imbalance(df: pd.DataFrame, target_column: Optional[str]) -> Dict[str, Any]:
    """Evaluates target class imbalance."""
    if not target_column or target_column not in df.columns:
        return {"status": "skipped", "reason": "No valid target column provided."}

    counts = df[target_column].value_counts()
    ratios = df[target_column].value_counts(normalize=True).to_dict()
    min_ratio = float(min(ratios.values())) if ratios else 0.0
    imbalanced = min_ratio < 0.20  # Under 20% minority class

    return {
        "status": "success",
        "target_column": target_column,
        "class_counts": {str(k): int(v) for k, v in counts.items()},
        "class_ratios": {str(k): float(round(v, 4)) for k, v in ratios.items()},
        "is_imbalanced": imbalanced,
        "minority_ratio": round(min_ratio, 4)
    }


def detect_identifier_columns(df: pd.DataFrame) -> List[str]:
    """Detects columns acting as high-cardinality patient or row identifiers."""
    id_cols = []
    for col in df.columns:
        clean = str(col).lower().strip()
        n_unique = df[col].nunique(dropna=True)
        if any(clean.startswith(p) or clean.endswith(p) for p in ["id", "_id", "guid", "uuid", "patient", "subject"]):
            if n_unique > len(df) * 0.90:
                id_cols.append(str(col))
    return id_cols


def detect_target_leakage(df: pd.DataFrame, target_column: Optional[str], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """Identifies features suspiciously correlated with the target."""
    if not target_column or target_column not in df.columns:
        return []

    target_series = df[target_column]
    if target_series.nunique() != 2:
        return []

    # Map binary target to 0/1 for correlation
    vals = list(target_series.dropna().unique())
    y = target_series.map({vals[0]: 0, vals[1]: 1})

    leakage_findings = []
    for col in df.columns:
        if col == target_column:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            corr = float(abs(df[col].corr(y)))
            if np.isnan(corr):
                continue
            if corr >= threshold:
                leakage_findings.append({
                    "feature": str(col),
                    "correlation_with_target": round(corr, 4),
                    "risk": "critical" if corr > 0.98 else "high"
                })
    return leakage_findings


def run_quality_analysis(df: pd.DataFrame, target_column: Optional[str] = None) -> DataQualityReport:
    """Executes all quality checks and aggregates structured findings."""
    missing = detect_missing_values(df)
    duplicates = detect_duplicates(df)
    invalid = detect_invalid_values(df)
    inconsistent = detect_inconsistent_categories(df)
    outliers = detect_outliers(df)
    constants = detect_constant_features(df)
    high_corr = detect_high_correlations(df)
    imbalance = detect_class_imbalance(df, target_column)
    leakage = detect_target_leakage(df, target_column)

    findings: List[QualityFinding] = []
    warnings: List[str] = []

    if missing["has_missing"]:
        findings.append(QualityFinding(
            severity="warning",
            category="missing_values",
            affected_columns=missing["affected_columns"],
            description=f"Detected {missing['total_missing']} missing values across {len(missing['affected_columns'])} columns.",
            recommended_action="Impute with median (numerical) or mode/constant (categorical)."
        ))
        warnings.append(f"Missing values detected in {len(missing['affected_columns'])} columns.")

    if duplicates["has_duplicates"]:
        findings.append(QualityFinding(
            severity="info",
            category="duplicates",
            affected_columns=[],
            description=f"Found {duplicates['duplicate_count']} exact duplicate rows ({duplicates['duplicate_ratio']*100:.1f}%).",
            recommended_action="Remove duplicate rows to prevent bias and train/test leakage."
        ))

    if inconsistent["has_inconsistencies"]:
        cols = list(inconsistent["inconsistent_columns"].keys())
        findings.append(QualityFinding(
            severity="warning",
            category="inconsistent_categories",
            affected_columns=cols,
            description=f"Inconsistent categorical casing found in {cols}.",
            recommended_action="Normalize strings by trimming whitespace and lowercasing."
        ))

    if constants["has_constants"]:
        findings.append(QualityFinding(
            severity="warning",
            category="constant_features",
            affected_columns=constants["constant_columns"],
            description=f"Constant columns with zero variance: {constants['constant_columns']}",
            recommended_action="Drop constant columns as they provide no discriminative information."
        ))

    if imbalance.get("is_imbalanced"):
        findings.append(QualityFinding(
            severity="warning",
            category="class_imbalance",
            affected_columns=[target_column] if target_column else [],
            description=f"Class imbalance detected. Minority class ratio: {imbalance['minority_ratio']*100:.1f}%.",
            recommended_action="Employ stratified train/test splitting and evaluate balanced metrics."
        ))

    if leakage:
        findings.append(QualityFinding(
            severity="critical",
            category="target_leakage",
            affected_columns=[f["feature"] for f in leakage],
            description=f"Suspected target leakage detected in {[f['feature'] for f in leakage]} with correlation > 0.95.",
            recommended_action="Exclude leaking columns from feature set."
        ))
        warnings.append(f"Target leakage risk in {[f['feature'] for f in leakage]}.")

    return DataQualityReport(
        status="success",
        missing_value_summary=missing,
        duplicate_summary=duplicates,
        invalid_value_summary=invalid,
        inconsistent_categories_summary=inconsistent,
        outlier_summary=outliers,
        constant_feature_summary=constants,
        high_correlation_pairs=high_corr,
        class_imbalance_summary=imbalance,
        target_leakage_risk=leakage,
        findings=findings,
        warnings=warnings
    )
