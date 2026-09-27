"""Conditional routing functions for LangGraph workflow execution."""

from typing import Literal
from .state import PreprocessingState


def route_approval_gate(state: PreprocessingState) -> Literal["execute_preprocessing", "request_changes", "approval_gate"]:
    """Routes based on human approval decision."""
    status = state.get("approval_status", "pending")
    if status == "approved":
        return "execute_preprocessing"
    elif status == "rejected":
        return "request_changes"
    return "approval_gate"


def route_after_validation(state: PreprocessingState) -> Literal["generate_report", "analyze_failure"]:
    """Routes based on validation outcome."""
    val_res = state.get("validation_result")
    if val_res and val_res.passed:
        return "generate_report"
    return "analyze_failure"


def route_after_failure_analysis(state: PreprocessingState) -> Literal["retry_node", "generate_report"]:
    """Routes based on recoverability and retry budget."""
    recoverable = state.get("recoverable", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if recoverable and retry_count < max_retries:
        return "retry_node"
    return "generate_report"
