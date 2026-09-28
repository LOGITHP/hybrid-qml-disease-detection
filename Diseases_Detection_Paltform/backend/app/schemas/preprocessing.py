from typing_extensions import Annotated
"""Preprocessing configuration, plan, and run execution schemas."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BeforeValidator, BaseModel, Field


class PreprocessingConfigCreate(BaseModel):
    """Custom user-defined preprocessing configuration."""
    name: str
    mode: Literal["auto", "user_defined"] = "auto"
    configuration: Dict[str, Any] = Field(default_factory=dict)


class PreprocessingPlanStep(BaseModel):
    """Discrete deterministic transformation step within an execution plan."""
    step_id: int
    tool_name: str
    rationale: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    fit_on_train_only: bool = True


class PreprocessingPlan(BaseModel):
    """Generated or user-defined preprocessing plan requiring human approval."""
    dataset_id: str
    dataset_version_id: str
    steps: List[PreprocessingPlanStep]
    summary: str
    leakage_prevention_guarantee: str = "Learned transformers (imputer, scaler, encoder) are fit strictly on X_train."


class PreprocessingRunCreate(BaseModel):
    """Initiate a preprocessing run."""
    dataset_version_id: str
    mode: Literal["auto", "user_defined"] = "auto"
    preprocessing_config_id: Optional[str] = None
    user_defined_plan: Optional[PreprocessingPlan] = None


class PreprocessingRunResponse(BaseModel):
    """State and artifacts of a preprocessing execution."""
    id: Annotated[str, BeforeValidator(str)]
    dataset_version_id: str
    user_id: str
    status: str  # pending, planning, awaiting_approval, running, completed, failed
    approval_status: str  # not_required, pending, approved, rejected
    plan: Optional[Dict[str, Any]] = None
    report_artifact_id: Optional[str] = None
    processed_artifact_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlanApprovalRequest(BaseModel):
    """Action payload for human-in-the-loop plan confirmation."""
    approved: bool
    feedback: Optional[str] = None
