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
    step_id: str | int
    tool_name: str
    rationale: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    fit_on_train_only: bool = True


class PreprocessingPlan(BaseModel):
    """Generated or user-defined preprocessing plan (acts as the unified PipelineConfig)."""
    dataset_id: str
    dataset_version_id: str
    target_column: Optional[str] = None
    steps: List[PreprocessingPlanStep]
    summary: str = ""
    leakage_prevention_guarantee: str = "Learned transformers (imputer, scaler, encoder) are fit strictly on X_train."
    generation_method: Literal["rule_based", "llm", "user_defined"] = "rule_based"
    generation_provider: Optional[str] = None
    generation_note: str = ""


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


class AIModifyRequest(BaseModel):
    """Payload for natural-language modification of a preprocessing pipeline."""
    dataset_id: str
    dataset_version_id: str
    current_pipeline: PreprocessingPlan
    user_instruction: str


class AILogicChange(BaseModel):
    action: Literal["add", "remove", "replace", "update"]
    step_id: str
    new_operation: Optional[PreprocessingPlanStep] = None
    config_update: Optional[Dict[str, Any]] = None
    reason: str


class AIModifyResponse(BaseModel):
    """Structured response from the LLM after processing natural language pipeline modification."""
    status: Literal["valid", "invalid"]
    explanation: str
    changes: List[AILogicChange]
    updated_pipeline: Optional[PreprocessingPlan] = None
    warnings: List[str] = Field(default_factory=list)
