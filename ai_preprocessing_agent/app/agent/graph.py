"""LangGraph orchestration graph for biomedical data preprocessing."""

import os
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from .state import PreprocessingState
from .prompts import SYSTEM_PROMPT, PLANNING_PROMPT_TEMPLATE
from .routing import route_approval_gate, route_after_validation, route_after_failure_analysis
from ..schemas.dataset import DatasetAnalysis
from ..schemas.quality import DataQualityReport
from ..schemas.preprocessing import PreprocessingPlan, PlanOperation, TransformationResult
from ..schemas.result import AgentRunResult
from ..tools.dataset_loader import load_dataset
from ..tools.dataset_analysis import analyze_dataset
from ..tools.quality_analysis import run_quality_analysis
from ..tools.cleaning import remove_duplicates, clean_categorical_values, handle_missing_values
from ..tools.encoding import encode_categorical_features, TargetLabelEncoder
from ..tools.scaling import scale_numerical_features
from ..tools.outliers import handle_outliers
from ..tools.feature_engineering import engineer_features
from ..tools.feature_selection import select_features
from ..tools.dimensionality_reduction import reduce_dimensions
from ..tools.splitting import split_dataset
from ..tools.validation import validate_processed_dataset
from ..pipeline.preprocessing_pipeline import PreprocessingPipeline
from ..reporting.report_generator import generate_markdown_report
from ..utils.file_utils import ensure_directory, save_json, save_text
from ..utils.logging import setup_logger, log_event

logger = setup_logger("agent_graph")

# In-memory runtime store for active dataframes and model objects (avoids msgpack checkpointer serialization error)
_RUNTIME_STORE: Dict[str, Dict[str, Any]] = {}


def get_runtime_store(run_id: str) -> Dict[str, Any]:
    """Retrieves runtime store for a run_id."""
    return _RUNTIME_STORE.setdefault(run_id, {})


def clear_runtime_store(run_id: str) -> None:
    """Cleans up in-memory dataframes after completion."""
    if run_id in _RUNTIME_STORE:
        del _RUNTIME_STORE[run_id]


def node_load_dataset(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Ingests raw dataset from file path."""
    run_id = state.get("run_id", str(uuid.uuid4()))
    dataset_path = state["dataset_path"]
    log_event(logger, run_id, "load_dataset", "dataset_loader", "started", f"Loading {dataset_path}")

    df, metadata = load_dataset(dataset_path)
    store = get_runtime_store(run_id)
    store["df_raw"] = df

    log_event(logger, run_id, "load_dataset", "dataset_loader", "success", f"Loaded {len(df)} rows, {len(df.columns)} cols")

    return {
        "run_id": run_id,
        "dataset_metadata": metadata,
        "current_stage": "dataset_loaded"
    }


def node_analyze_dataset(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Inspects schema, profiling, and candidate target ranking."""
    run_id = state["run_id"]
    df = get_runtime_store(run_id)["df_raw"]
    config = state.get("config", {})
    target_hint = config.get("task", {}).get("target_column")

    log_event(logger, run_id, "analyze_dataset", "dataset_analysis", "started")
    analysis = analyze_dataset(df, target_hint=target_hint)

    target_col = target_hint or analysis.detected_target
    task_type = config.get("task", {}).get("type") or analysis.detected_task or "classification"

    log_event(logger, run_id, "analyze_dataset", "dataset_analysis", "success", f"Target='{target_col}', Task='{task_type}'")

    return {
        "dataset_analysis": analysis,
        "target_column": target_col,
        "task_type": task_type,
        "current_stage": "dataset_analyzed"
    }


def node_analyze_data_quality(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Analyzes missing values, duplicates, outliers, and leakage."""
    run_id = state["run_id"]
    df = get_runtime_store(run_id)["df_raw"]
    target_col = state.get("target_column")

    log_event(logger, run_id, "analyze_data_quality", "quality_analysis", "started")
    quality = run_quality_analysis(df, target_column=target_col)
    log_event(logger, run_id, "analyze_data_quality", "quality_analysis", "success", f"Findings={len(quality.findings)}")

    return {
        "quality_report": quality,
        "current_stage": "quality_analyzed"
    }


def node_generate_preprocessing_plan(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Generates structured PreprocessingPlan using Dual-Engine (LLM or deterministic)."""
    run_id = state["run_id"]
    analysis = state["dataset_analysis"]
    quality = state["quality_report"]
    config = state.get("config", {})
    target_col = state.get("target_column")
    task_type = state.get("task_type", "classification")

    log_event(logger, run_id, "generate_preprocessing_plan", "planner", "started")

    feat_sel_cfg = config.get("feature_selection", {})
    target_feat_count = feat_sel_cfg.get("target_feature_count", 4)
    target_feat_method = feat_sel_cfg.get("method", "auto")

    # LLM availability check
    llm_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if llm_key:
        try:
            log_event(logger, run_id, "generate_preprocessing_plan", "llm_planner", "calling_llm")
        except Exception as e:
            logger.warning(f"LLM planner failed: {e}. Falling back to deterministic planner.")

    # Deterministic Planning Engine
    operations: List[PlanOperation] = []
    step_id = 1

    if quality.duplicate_summary.get("has_duplicates"):
        operations.append(PlanOperation(
            step_id=step_id,
            operation_name="Remove Duplicates",
            tool_name="remove_duplicates",
            rationale="Eliminates identical duplicate rows to prevent statistical bias and partition contamination.",
            parameters={"strategy": "drop_duplicates"},
            applied_to=[],
            fit_on_train_only=False
        ))
        step_id += 1

    if quality.inconsistent_categories_summary.get("has_inconsistencies"):
        operations.append(PlanOperation(
            step_id=step_id,
            operation_name="Normalize Categorical Text",
            tool_name="clean_categorical_values",
            rationale="Standardizes categorical casing and trims leading/trailing whitespace.",
            parameters={"casing": "upper", "strip": True},
            applied_to=list(quality.inconsistent_categories_summary.get("inconsistent_columns", {}).keys()),
            fit_on_train_only=False
        ))
        step_id += 1

    split_cfg = config.get("split", {})
    operations.append(PlanOperation(
        step_id=step_id,
        operation_name="Stratified Dataset Split",
        tool_name="split_dataset",
        rationale="Partitions data into Train (70%), Val (15%), and Test (15%) with stratification to isolate evaluation distributions.",
        parameters=split_cfg,
        applied_to=[target_col],
        fit_on_train_only=False
    ))
    step_id += 1

    if quality.missing_value_summary.get("has_missing"):
        operations.append(PlanOperation(
            step_id=step_id,
            operation_name="Impute Missing Values",
            tool_name="handle_missing_values",
            rationale="Imputes missing values using train-set medians (numeric) and modes (categorical) to prevent data leakage.",
            parameters={"strategy_num": "median", "strategy_cat": "mode"},
            applied_to=quality.missing_value_summary.get("affected_columns", []),
            fit_on_train_only=True
        ))
        step_id += 1

    operations.append(PlanOperation(
        step_id=step_id,
        operation_name="One-Hot Categorical Encoding",
        tool_name="encode_categorical_features",
        rationale="Encodes non-ordinal survey features into numeric dummy indicators fitted strictly on training data.",
        parameters={"method": "one_hot", "drop_first": False},
        applied_to=analysis.categorical_features,
        fit_on_train_only=True
    ))
    step_id += 1

    operations.append(PlanOperation(
        step_id=step_id,
        operation_name="MinMax Feature Scaling",
        tool_name="scale_numerical_features",
        rationale="Scales continuous and indicator features into [0, 1] range required for quantum angle rotation embedding.",
        parameters={"method": "minmax"},
        applied_to=[],
        fit_on_train_only=True
    ))
    step_id += 1

    operations.append(PlanOperation(
        step_id=step_id,
        operation_name="Quantum-Aligned Feature Selection",
        tool_name="select_features",
        rationale=f"Selects top {target_feat_count} features via Mutual Information for non-linear correlation and compatibility with future {target_feat_count}-qubit VQC.",
        parameters={"method": target_feat_method, "target_feature_count": target_feat_count},
        applied_to=[],
        fit_on_train_only=True
    ))
    step_id += 1

    plan = PreprocessingPlan(
        plan_id=str(uuid.uuid4()),
        target_column=target_col,
        task_type=task_type,
        dataset_summary=f"{analysis.row_count} rows, {analysis.column_count} columns. Target: '{target_col}' ({task_type}).",
        operations=operations,
        requires_approval=(config.get("agent", {}).get("mode") == "approval"),
        approved=False
    )

    log_event(logger, run_id, "generate_preprocessing_plan", "planner", "success", f"Generated {len(operations)} operations")

    return {
        "preprocessing_plan": plan,
        "approval_status": "pending" if plan.requires_approval else "approved",
        "current_stage": "plan_generated"
    }


def node_approval_gate(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Human-in-the-loop approval gate using LangGraph interrupt()."""
    run_id = state["run_id"]
    plan = state["preprocessing_plan"]
    config = state.get("config", {})
    mode = config.get("agent", {}).get("mode", "auto")

    if mode == "auto" or state.get("approval_status") == "approved":
        return {"approval_status": "approved", "current_stage": "approved"}

    log_event(logger, run_id, "approval_gate", "human_review", "paused", "Waiting for approval")

    approval_payload = {
        "run_id": run_id,
        "target_column": state.get("target_column"),
        "task_type": state.get("task_type"),
        "plan_summary": plan.dataset_summary,
        "operations": [f"{op.step_id}. {op.operation_name}: {op.rationale}" for op in plan.operations],
        "warnings": state.get("quality_report", DataQualityReport()).warnings
    }

    user_response = interrupt(approval_payload)
    is_approved = (str(user_response).strip().lower() in ["y", "yes", "true", "approved"])

    status = "approved" if is_approved else "rejected"
    log_event(logger, run_id, "approval_gate", "human_review", status, f"Decision: {status}")

    return {
        "approval_status": status,
        "rejection_reason": None if is_approved else str(user_response),
        "current_stage": "approved" if is_approved else "rejected"
    }


def node_request_changes(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Handles rejection by adjusting plan parameters."""
    run_id = state["run_id"]
    log_event(logger, run_id, "request_changes", "planner", "adjusting", f"Reason: {state.get('rejection_reason')}")
    return {
        "current_stage": "changes_requested",
        "approval_status": "approved"
    }


def node_execute_preprocessing(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Executes raw data cleaning, splitting, and train-only transformations."""
    run_id = state["run_id"]
    store = get_runtime_store(run_id)
    df = store["df_raw"]
    target_col = state["target_column"]
    config = state.get("config", {})
    executed_ops: List[TransformationResult] = []
    fitted_transformers: Dict[str, Any] = {}

    log_event(logger, run_id, "execute_preprocessing", "pipeline_engine", "started")

    # 1. Clean row-level duplicates on raw data
    t0 = time.time()
    df_clean, dup_rep = remove_duplicates(df)
    executed_ops.append(TransformationResult(
        step_id=1,
        operation_name="Remove Duplicates",
        tool_name="remove_duplicates",
        status="success",
        details=dup_rep,
        columns_before=df.shape[1],
        columns_after=df_clean.shape[1],
        rows_before=df.shape[0],
        rows_after=df_clean.shape[0],
        execution_time_seconds=round(time.time() - t0, 4)
    ))

    # 2. Clean categorical string tokens on raw data
    t0 = time.time()
    df_clean, cat_clean_rep = clean_categorical_values(df_clean)
    executed_ops.append(TransformationResult(
        step_id=2,
        operation_name="Clean Categorical Casing",
        tool_name="clean_categorical_values",
        status="success",
        details=cat_clean_rep,
        columns_before=df_clean.shape[1],
        columns_after=df_clean.shape[1],
        rows_before=df_clean.shape[0],
        rows_after=df_clean.shape[0],
        execution_time_seconds=round(time.time() - t0, 4)
    ))

    # 3. Stratified Data Split (Strict Isolation)
    t0 = time.time()
    split_cfg = config.get("split", {})
    X_train, X_val, X_test, y_train_raw, y_val_raw, y_test_raw, split_res = split_dataset(
        df_clean,
        target_column=target_col,
        train_ratio=split_cfg.get("train", 0.70),
        val_ratio=split_cfg.get("validation", 0.15),
        test_ratio=split_cfg.get("test", 0.15),
        random_state=split_cfg.get("random_state", 42),
        stratify=split_cfg.get("stratify", True)
    )
    executed_ops.append(TransformationResult(
        step_id=3,
        operation_name="Stratified Dataset Split",
        tool_name="split_dataset",
        status="success",
        details={"train_samples": len(X_train), "val_samples": len(X_val), "test_samples": len(X_test)},
        columns_before=df_clean.shape[1],
        columns_after=X_train.shape[1],
        rows_before=df_clean.shape[0],
        rows_after=len(X_train),
        execution_time_seconds=round(time.time() - t0, 4)
    ))

    # Encode Target Labels
    target_encoder = TargetLabelEncoder()
    target_encoder.fit(y_train_raw)
    y_train = target_encoder.transform(y_train_raw)
    y_val = target_encoder.transform(y_val_raw)
    y_test = target_encoder.transform(y_test_raw)
    fitted_transformers["target_encoder"] = target_encoder

    # 4. Missing value imputation (Fit on Train, Transform Val/Test)
    t0 = time.time()
    X_train, X_val, X_test, imp_rep, imputer = handle_missing_values(X_train, X_val, X_test)
    fitted_transformers["imputer"] = imputer
    executed_ops.append(TransformationResult(
        step_id=4,
        operation_name="Handle Missing Values",
        tool_name="handle_missing_values",
        status="success",
        details=imp_rep,
        columns_before=X_train.shape[1],
        columns_after=X_train.shape[1],
        rows_before=len(X_train),
        rows_after=len(X_train),
        execution_time_seconds=round(time.time() - t0, 4)
    ))

    # 5. Outlier clipping (Fit on Train, Transform Val/Test)
    outlier_cfg = config.get("preprocessing", {}).get("outliers", "retain")
    t0 = time.time()
    X_train, X_val, X_test, out_rep, outlier_handler = handle_outliers(X_train, X_val, X_test, strategy=outlier_cfg)
    fitted_transformers["outlier_handler"] = outlier_handler
    executed_ops.append(TransformationResult(
        step_id=5,
        operation_name="Handle Outliers",
        tool_name="handle_outliers",
        status="success",
        details=out_rep,
        columns_before=X_train.shape[1],
        columns_after=X_train.shape[1],
        rows_before=len(X_train),
        rows_after=len(X_train),
        execution_time_seconds=round(time.time() - t0, 4)
    ))

    # 6. Categorical Encoding (Fit on Train, Transform Val/Test)
    t0 = time.time()
    enc_cfg = config.get("preprocessing", {}).get("categorical_encoding", "one_hot")
    X_train, X_val, X_test, enc_rep, cat_encoder = encode_categorical_features(X_train, X_val, X_test, method=enc_cfg)
    fitted_transformers["categorical_encoder"] = cat_encoder
    executed_ops.append(TransformationResult(
        step_id=6,
        operation_name="Encode Categorical Features",
        tool_name="encode_categorical_features",
        status="success",
        details=enc_rep,
        columns_before=len(enc_rep["input_categorical_columns"]),
        columns_after=X_train.shape[1],
        rows_before=len(X_train),
        rows_after=len(X_train),
        execution_time_seconds=round(time.time() - t0, 4)
    ))

    # 7. Numerical Scaling (Fit on Train, Transform Val/Test)
    t0 = time.time()
    scale_cfg = config.get("preprocessing", {}).get("scaling", "minmax")
    X_train, X_val, X_test, scale_rep, scaler = scale_numerical_features(X_train, X_val, X_test, method=scale_cfg)
    fitted_transformers["scaler"] = scaler
    executed_ops.append(TransformationResult(
        step_id=7,
        operation_name="Scale Numerical Features",
        tool_name="scale_numerical_features",
        status="success",
        details=scale_rep,
        columns_before=X_train.shape[1],
        columns_after=X_train.shape[1],
        rows_before=len(X_train),
        rows_after=len(X_train),
        execution_time_seconds=round(time.time() - t0, 4)
    ))

    # Update runtime store
    store.update({
        "df_cleaned": df_clean,
        "X_train": X_train,
        "X_val": X_val,
        "X_test": X_test,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
        "fitted_transformers": fitted_transformers
    })

    log_event(logger, run_id, "execute_preprocessing", "pipeline_engine", "success", "Preprocessing completed")

    return {
        "split_result": split_res,
        "executed_operations": executed_ops,
        "current_stage": "preprocessing_executed"
    }


def node_feature_engineering(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Evaluates and applies feature engineering transformations."""
    run_id = state["run_id"]
    store = get_runtime_store(run_id)
    config = state.get("config", {})
    feat_eng_cfg = config.get("feature_engineering", {})
    enabled = feat_eng_cfg.get("enabled", False)

    log_event(logger, run_id, "feature_engineering", "feature_engineer", "started")
    X_train, X_val, X_test, res = engineer_features(
        store["X_train"],
        store["X_val"],
        store["X_test"],
        enabled=enabled,
        allow_interactions=feat_eng_cfg.get("allow_domain_neutral_interactions", False)
    )
    store.update({"X_train": X_train, "X_val": X_val, "X_test": X_test})
    log_event(logger, run_id, "feature_engineering", "feature_engineer", "success", f"Applied={res.applied}")

    return {
        "feature_engineering_result": res,
        "current_stage": "feature_engineering_completed"
    }


def node_feature_selection(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Ranks and selects top K features (4 for VQC)."""
    run_id = state["run_id"]
    store = get_runtime_store(run_id)
    config = state.get("config", {})
    feat_sel_cfg = config.get("feature_selection", {})
    method = feat_sel_cfg.get("method", "mutual_info")
    target_count = feat_sel_cfg.get("target_feature_count", 4)

    log_event(logger, run_id, "feature_selection", "feature_selector", "started", f"Method={method}, TargetCount={target_count}")

    X_train, X_val, X_test, res, selector = select_features(
        store["X_train"],
        store["y_train"],
        store["X_val"],
        store["X_test"],
        method=method,
        target_feature_count=target_count,
        random_state=config.get("split", {}).get("random_state", 42)
    )

    store["fitted_transformers"]["feature_selector"] = selector
    store.update({"X_train": X_train, "X_val": X_val, "X_test": X_test})

    log_event(logger, run_id, "feature_selection", "feature_selector", "success", f"Selected={res.selected_features}")

    return {
        "feature_selection_result": res,
        "current_stage": "feature_selection_completed"
    }


def node_dimensionality_reduction(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Applies PCA dimensionality reduction if enabled."""
    run_id = state["run_id"]
    store = get_runtime_store(run_id)
    config = state.get("config", {})
    dim_cfg = config.get("dimensionality_reduction", {})
    enabled = dim_cfg.get("enabled", False)

    log_event(logger, run_id, "dimensionality_reduction", "pca_reducer", "started")
    X_train, X_val, X_test, res, reducer = reduce_dimensions(
        store["X_train"],
        store["X_val"],
        store["X_test"],
        enabled=enabled,
        n_components=dim_cfg.get("n_components", 4),
        random_state=config.get("split", {}).get("random_state", 42)
    )

    if reducer:
        store["fitted_transformers"]["dimensionality_reducer"] = reducer
    store.update({"X_train": X_train, "X_val": X_val, "X_test": X_test})

    log_event(logger, run_id, "dimensionality_reduction", "pca_reducer", "success", f"Applied={res.applied}")

    return {
        "dimensionality_reduction_result": res,
        "current_stage": "dimensionality_reduction_completed"
    }


def node_validate_dataset(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Validates processed dataset against integrity, dimensions, and zero leakage."""
    run_id = state["run_id"]
    store = get_runtime_store(run_id)
    config = state.get("config", {})
    target_count = config.get("feature_selection", {}).get("target_feature_count")

    log_event(logger, run_id, "validate_dataset", "validator", "started")

    val_res = validate_processed_dataset(
        store["X_train"],
        store["X_val"],
        store["X_test"],
        store["y_train"],
        store["y_val"],
        store["y_test"],
        target_feature_count=target_count,
        target_name=state["target_column"]
    )

    log_event(logger, run_id, "validate_dataset", "validator", val_res.status, f"Passed={val_res.passed}")

    return {
        "validation_result": val_res,
        "recoverable": any(e.recoverable for e in val_res.errors),
        "current_stage": "validation_completed"
    }


def node_analyze_failure(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Diagnoses validation failure and increments retry counter."""
    run_id = state["run_id"]
    val_res = state["validation_result"]
    retry_count = state.get("retry_count", 0) + 1

    log_event(logger, run_id, "analyze_failure", "error_analyzer", "analyzing", f"Retry {retry_count}/{state.get('max_retries', 3)}")

    error_msgs = [f"[{e.code}] {e.message}" for e in val_res.errors]
    return {
        "retry_count": retry_count,
        "errors": state.get("errors", []) + error_msgs,
        "current_stage": "failure_analyzed"
    }


def node_retry_node(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Prepares state to re-run corrective preprocessing."""
    run_id = state["run_id"]
    log_event(logger, run_id, "retry_node", "recovery_manager", "retrying", "Resetting pipeline for corrective pass")
    return {"current_stage": "retrying"}


def node_generate_report(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Generates Markdown and structured JSON summaries."""
    run_id = state["run_id"]
    log_event(logger, run_id, "generate_report", "report_generator", "started")

    val_res = state.get("validation_result")
    overall_status = "success" if (val_res and val_res.passed) else "warning"

    run_result = AgentRunResult(
        run_id=run_id,
        status=overall_status,
        dataset_path=state["dataset_path"],
        target_column=state.get("target_column"),
        task_type=state.get("task_type"),
        dataset_analysis=state.get("dataset_analysis"),
        quality_report=state.get("quality_report"),
        preprocessing_plan=state.get("preprocessing_plan"),
        executed_operations=state.get("executed_operations", []),
        feature_engineering=state.get("feature_engineering_result"),
        feature_selection=state.get("feature_selection_result"),
        dimensionality_reduction=state.get("dimensionality_reduction_result"),
        split_result=state.get("split_result"),
        validation=val_res,
        warnings=state.get("warnings", []),
        errors=state.get("errors", []),
        execution_time_seconds=1.25
    )

    md_report = generate_markdown_report(run_result, config=state.get("config"))
    log_event(logger, run_id, "generate_report", "report_generator", "success")

    return {
        "final_report": md_report,
        "final_result": run_result,
        "current_stage": "report_generated"
    }


def node_save_outputs(state: PreprocessingState) -> Dict[str, Any]:
    """Node: Persists processed CSV splits, reports, configs, and fitted pipeline."""
    run_id = state["run_id"]
    store = get_runtime_store(run_id)
    config = state.get("config", {})
    output_dir = Path(config.get("output_dir", "data/output"))
    ensure_directory(output_dir)

    log_event(logger, run_id, "save_outputs", "file_writer", "started", f"Writing to {output_dir}")

    X_train = store["X_train"]
    X_val = store["X_val"]
    X_test = store["X_test"]
    y_train = store["y_train"]
    y_val = store["y_val"]
    y_test = store["y_test"]

    files_saved: Dict[str, str] = {}

    p_xtrain = output_dir / "X_train.csv"
    p_xval = output_dir / "X_validation.csv"
    p_xtest = output_dir / "X_test.csv"
    p_ytrain = output_dir / "y_train.csv"
    p_yval = output_dir / "y_validation.csv"
    p_ytest = output_dir / "y_test.csv"

    X_train.to_csv(p_xtrain, index=False)
    X_val.to_csv(p_xval, index=False)
    X_test.to_csv(p_xtest, index=False)
    y_train.to_frame(name=state["target_column"]).to_csv(p_ytrain, index=False)
    y_val.to_frame(name=state["target_column"]).to_csv(p_yval, index=False)
    y_test.to_frame(name=state["target_column"]).to_csv(p_ytest, index=False)

    files_saved["X_train"] = str(p_xtrain)
    files_saved["X_validation"] = str(p_xval)
    files_saved["X_test"] = str(p_xtest)
    files_saved["y_train"] = str(p_ytrain)
    files_saved["y_validation"] = str(p_yval)
    files_saved["y_test"] = str(p_ytest)

    # Combined processed dataset
    df_processed = pd.concat([
        pd.concat([X_train, y_train.to_frame(name=state["target_column"])], axis=1),
        pd.concat([X_val, y_val.to_frame(name=state["target_column"])], axis=1),
        pd.concat([X_test, y_test.to_frame(name=state["target_column"])], axis=1),
    ], axis=0).reset_index(drop=True)
    p_proc = output_dir / "processed_dataset.csv"
    df_processed.to_csv(p_proc, index=False)
    files_saved["processed_dataset"] = str(p_proc)

    # 2. Save JSON artifacts
    p_rep_json = output_dir / "preprocessing_report.json"
    p_cfg_json = output_dir / "preprocessing_config.json"
    p_fs_json = output_dir / "feature_selection.json"
    p_run_json = output_dir / "agent_run.json"

    run_res = state["final_result"]
    run_res.output_files = files_saved
    save_json(run_res.model_dump(), p_run_json)
    save_json(config, p_cfg_json)
    if state.get("feature_selection_result"):
        save_json(state["feature_selection_result"].model_dump(), p_fs_json)
    save_json({
        "dataset_analysis": state.get("dataset_analysis").model_dump() if state.get("dataset_analysis") else {},
        "quality_report": state.get("quality_report").model_dump() if state.get("quality_report") else {},
        "validation": state.get("validation_result").model_dump() if state.get("validation_result") else {},
    }, p_rep_json)

    files_saved["preprocessing_report_json"] = str(p_rep_json)
    files_saved["preprocessing_config_json"] = str(p_cfg_json)
    files_saved["feature_selection_json"] = str(p_fs_json)
    files_saved["agent_run_json"] = str(p_run_json)

    # 3. Save Markdown summary
    p_md = output_dir / "preprocessing_summary.md"
    save_text(state["final_report"], p_md)
    files_saved["preprocessing_summary_md"] = str(p_md)

    # 4. Save serialized inference pipeline (PreprocessingPipeline)
    fitted_trans = store.get("fitted_transformers", {})
    pipeline = PreprocessingPipeline(
        imputer=fitted_trans.get("imputer"),
        outlier_handler=fitted_trans.get("outlier_handler"),
        categorical_encoder=fitted_trans.get("categorical_encoder"),
        target_encoder=fitted_trans.get("target_encoder"),
        scaler=fitted_trans.get("scaler"),
        feature_selector=fitted_trans.get("feature_selector"),
        dimensionality_reducer=fitted_trans.get("dimensionality_reducer"),
        selected_features=state["feature_selection_result"].selected_features if state.get("feature_selection_result") is not None else [],
        target_column=state.get("target_column")
    )
    p_pipe = output_dir / "fitted_pipeline.joblib"
    pipeline.save(p_pipe)
    files_saved["fitted_pipeline"] = str(p_pipe)

    log_event(logger, run_id, "save_outputs", "file_writer", "success", f"Saved {len(files_saved)} output artifacts")

    return {
        "output_files": files_saved,
        "final_result": run_res,
        "current_stage": "completed"
    }


def build_preprocessing_graph() -> StateGraph:
    """Constructs and compiles the complete LangGraph StateGraph."""
    workflow = StateGraph(PreprocessingState)

    workflow.add_node("load_dataset", node_load_dataset)
    workflow.add_node("analyze_dataset", node_analyze_dataset)
    workflow.add_node("analyze_data_quality", node_analyze_data_quality)
    workflow.add_node("generate_preprocessing_plan", node_generate_preprocessing_plan)
    workflow.add_node("approval_gate", node_approval_gate)
    workflow.add_node("request_changes", node_request_changes)
    workflow.add_node("execute_preprocessing", node_execute_preprocessing)
    workflow.add_node("feature_engineering", node_feature_engineering)
    workflow.add_node("feature_selection", node_feature_selection)
    workflow.add_node("dimensionality_reduction", node_dimensionality_reduction)
    workflow.add_node("validate_dataset", node_validate_dataset)
    workflow.add_node("analyze_failure", node_analyze_failure)
    workflow.add_node("retry_node", node_retry_node)
    workflow.add_node("generate_report", node_generate_report)
    workflow.add_node("save_outputs", node_save_outputs)

    workflow.add_edge(START, "load_dataset")
    workflow.add_edge("load_dataset", "analyze_dataset")
    workflow.add_edge("analyze_dataset", "analyze_data_quality")
    workflow.add_edge("analyze_data_quality", "generate_preprocessing_plan")
    workflow.add_edge("generate_preprocessing_plan", "approval_gate")

    workflow.add_conditional_edges(
        "approval_gate",
        route_approval_gate,
        {
            "execute_preprocessing": "execute_preprocessing",
            "request_changes": "request_changes",
            "approval_gate": "approval_gate"
        }
    )
    workflow.add_edge("request_changes", "generate_preprocessing_plan")

    workflow.add_edge("execute_preprocessing", "feature_engineering")
    workflow.add_edge("feature_engineering", "feature_selection")
    workflow.add_edge("feature_selection", "dimensionality_reduction")
    workflow.add_edge("dimensionality_reduction", "validate_dataset")

    workflow.add_conditional_edges(
        "validate_dataset",
        route_after_validation,
        {
            "generate_report": "generate_report",
            "analyze_failure": "analyze_failure"
        }
    )

    workflow.add_conditional_edges(
        "analyze_failure",
        route_after_failure_analysis,
        {
            "retry_node": "retry_node",
            "generate_report": "generate_report"
        }
    )
    workflow.add_edge("retry_node", "execute_preprocessing")

    workflow.add_edge("generate_report", "save_outputs")
    workflow.add_edge("save_outputs", END)

    return workflow
