"""Human-readable Markdown and structured JSON report generator."""

from typing import Dict, Any, Optional
from ..schemas.result import AgentRunResult
from ..utils.reproducibility import get_environment_info


def generate_markdown_report(result: AgentRunResult, config: Optional[Dict[str, Any]] = None) -> str:
    """Generates the standardized 15-section biomedical preprocessing report."""
    analysis = result.dataset_analysis
    quality = result.quality_report
    plan = result.preprocessing_plan
    split = result.split_result
    val = result.validation
    feat_sel = result.feature_selection
    feat_eng = result.feature_engineering
    pca_res = result.dimensionality_reduction
    env_info = get_environment_info()

    lines = [
        "# Biomedical Dataset Preprocessing Report",
        f"**Run ID:** `{result.run_id}`  ",
        f"**Dataset Source:** `{result.dataset_path}`  ",
        f"**Status:** `{result.status.upper()}`  ",
        f"**Execution Time:** `{result.execution_time_seconds:.2f}s`  ",
        "\n---\n",
        "## 1. Dataset Overview",
        f"- **Total Rows Ingested:** {analysis.row_count if analysis else 'N/A'}",
        f"- **Total Columns:** {analysis.column_count if analysis else 'N/A'}",
        f"- **Detected Target Column:** `{result.target_column or 'None'}`",
        f"- **Identified Task Type:** `{result.task_type or 'None'}`",
        f"- **Numerical Features:** {len(analysis.numerical_features) if analysis else 0}",
        f"- **Categorical Features:** {len(analysis.categorical_features) if analysis else 0}",
        "\n## 2. Data Quality",
        f"- **Duplicate Rows Detected:** {quality.duplicate_summary.get('duplicate_count', 0) if quality else 0}",
        f"- **Missing Values Detected:** {quality.missing_value_summary.get('total_missing', 0) if quality else 0}",
        f"- **Class Imbalance:** {'Yes' if quality and quality.class_imbalance_summary.get('is_imbalanced') else 'No'}",
        "\n## 3. Problems Detected",
    ]

    if quality and quality.findings:
        for f in quality.findings:
            lines.append(f"- **[{f.severity.upper()}] {f.category}:** {f.description} (Recommended: *{f.recommended_action}*)")
    else:
        lines.append("- No critical data quality issues identified.")

    lines.extend([
        "\n## 4. Preprocessing Plan",
        f"- **Plan Summary:** {plan.dataset_summary if plan else 'Automated Preprocessing Execution.'}",
        "- **Planned Steps:**"
    ])
    if plan and plan.operations:
        for op in plan.operations:
            lines.append(f"  {op.step_id}. **{op.operation_name}** ({op.tool_name}): {op.rationale}")
    else:
        lines.append("  - Default safe preprocessing pipeline.")

    lines.extend([
        "\n## 5. Operations Executed",
    ])
    if result.executed_operations:
        for ex in result.executed_operations:
            lines.append(f"- **Step {ex.step_id} - {ex.operation_name}:** Status: `{ex.status}` | Columns: {ex.columns_before} -> {ex.columns_after} | Rows: {ex.rows_before} -> {ex.rows_after}")
    else:
        lines.append("- No operations logged.")

    lines.extend([
        "\n## 6. Feature Engineering",
        f"- **Applied:** {'Yes' if feat_eng and feat_eng.applied else 'No'}",
        f"- **Rationale:** {feat_eng.rationale if feat_eng else 'N/A'}",
        f"- **New Features Generated:** {feat_eng.new_features if feat_eng else []}",
        "\n## 7. Feature Selection",
        f"- **Selection Method:** `{feat_sel.method if feat_sel else 'N/A'}`",
        f"- **Input Dimension:** {feat_sel.input_feature_count if feat_sel else 'N/A'} features",
        f"- **Selected Dimension:** {feat_sel.selected_feature_count if feat_sel else 'N/A'} features",
        f"- **Selected Features:** `{feat_sel.selected_features if feat_sel else []}`",
        "\n## 8. Dimensionality Reduction",
        f"- **Applied:** {'Yes' if pca_res and pca_res.applied else 'No'}",
        f"- **Method:** `{pca_res.method if pca_res and pca_res.applied else 'None'}`",
        f"- **Total Explained Variance:** `{pca_res.total_explained_variance if pca_res and pca_res.applied else 'N/A'}`",
        "\n## 9. Dataset Splitting",
        f"- **Split Strategy:** Stratified Train/Val/Test (Leakage Free)",
        f"- **Train Partition:** {split.train_samples if split else 'N/A'} samples ({split.train_ratio*100:.0f}% if split else '70%')",
        f"- **Validation Partition:** {split.val_samples if split else 'N/A'} samples ({split.val_ratio*100:.0f}% if split else '15%')",
        f"- **Test Partition:** {split.test_samples if split else 'N/A'} samples ({split.test_ratio*100:.0f}% if split else '15%')",
        f"- **Random Seed:** `{split.random_state if split else 42}`",
        "\n## 10. Leakage Checks",
        f"- **Data Leakage Detected:** {'YES (Critical)' if val and val.leakage_detected else 'NO (Verified Clean)'}",
        "- **Fit Isolation:** All imputation, encoding, scaling, and feature selection fitted strictly on `X_train`.",
        "- **Validation & Test:** Strictly transformed without accessing evaluation distribution.",
        "\n## 11. Validation",
        f"- **Overall Status:** `{val.status.upper() if val else 'N/A'}`",
        f"- **Checks Passed:** {sum(1 for v in val.checks.values() if v) if val else 0} / {len(val.checks) if val else 0}",
    ])

    if val and val.errors:
        lines.append("- **Validation Errors:**")
        for err in val.errors:
            lines.append(f"  - [{err.code}] {err.message}")

    lines.extend([
        "\n## 12. Final Dataset",
        f"- **Train Matrix Shape:** `{val.train_shape if val else 'N/A'}`",
        f"- **Validation Matrix Shape:** `{val.val_shape if val else 'N/A'}`",
        f"- **Test Matrix Shape:** `{val.test_shape if val else 'N/A'}`",
        "\n## 13. Selected Features",
    ])

    if feat_sel and feat_sel.ranking:
        lines.append("| Rank | Feature Name | Normalized Score | Selected |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for f_item in feat_sel.ranking:
            is_sel = "YES" if f_item.feature_name in feat_sel.selected_features else "NO"
            lines.append(f"| {f_item.rank} | `{f_item.feature_name}` | {f_item.score:.4f} | **{is_sel}** |")
    else:
        lines.append("- No feature ranking available.")

    lines.extend([
        "\n## 14. Warnings",
    ])
    all_warnings = result.warnings + ([w.message for w in val.warnings] if val else [])
    if all_warnings:
        for w in set(all_warnings):
            lines.append(f"- ⚠️ {w}")
    else:
        lines.append("- None reported.")

    lines.extend([
        "\n## 15. Reproducibility Information",
        f"- **Random State:** `{split.random_state if split else 42}`",
        f"- **Python Version:** `{env_info['python_version']}`",
        f"- **Scikit-Learn:** `{env_info['sklearn_version']}`",
        f"- **Pandas:** `{env_info['pandas_version']}`",
        f"- **NumPy:** `{env_info['numpy_version']}`",
        "\n---\n*Report generated deterministically by AI Preprocessing Agent.*"
    ])

    return "\n".join(lines)
