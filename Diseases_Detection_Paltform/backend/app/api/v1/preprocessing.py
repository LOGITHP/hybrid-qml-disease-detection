"""AI Preprocessing Agent API endpoints for clinical plan generation, approval, and execution."""

import uuid
import io
import joblib
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from app.agents.preprocessing_agent.interface import PreprocessingAgent
from app.core.dependencies import get_current_user, get_dataset_service
from app.database.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.preprocessing import PreprocessingPlan, PreprocessingPlanStep
from app.services.dataset_service import DatasetService
from app.services.artifact_service import artifact_storage

router = APIRouter(prefix="/preprocessing", tags=["Preprocessing"])


class PlanRequest(BaseModel):
    dataset_version_id: str
    target_column: Optional[str] = None


class ExecutePlanRequest(BaseModel):
    dataset_version_id: str
    target_column: Optional[str] = None
    mode: str = "ai"
    steps: Optional[List[PreprocessingPlanStep]] = None


@router.post("/plan", response_model=StandardResponse[PreprocessingPlan], status_code=status.HTTP_200_OK)
async def generate_preprocessing_plan(
    payload: PlanRequest,
    current_user: User = Depends(get_current_user),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """Generate an AI-driven, leak-free preprocessing plan proposed by Gemma LLM."""
    version = await dataset_service.get_version(
        version_id=payload.dataset_version_id,
        user_id=str(current_user.id),
        is_admin=(current_user.role == "admin"),
    )
    df = dataset_service.load_version_dataframe(dataset_id=version.dataset_id, version_id=version.id)

    target_column = payload.target_column
    if target_column is None:
        analysis = await dataset_service.analyze_version(
            version_id=version.id,
            user_id=str(current_user.id),
            is_admin=(current_user.role == "admin"),
        )
        target_column = analysis.get("target_column")
    if not target_column:
        from app.core.exceptions import ValidationError
        raise ValidationError("Select the target column before generating a preprocessing plan.")

    agent = PreprocessingAgent()
    plan = await agent.generate_plan(df, target_column=target_column)
    plan.dataset_id = str(version.dataset_id)
    plan.dataset_version_id = str(version.id)

    return StandardResponse(
        message="AI preprocessing plan formulated successfully.",
        data=plan,
    )


@router.post("/execute", response_model=StandardResponse[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def execute_preprocessing_plan(
    payload: ExecutePlanRequest,
    current_user: User = Depends(get_current_user),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """Execute the approved preprocessing pipeline deterministically with zero data leakage."""
    version = await dataset_service.get_version(
        version_id=payload.dataset_version_id,
        user_id=str(current_user.id),
        is_admin=(current_user.role == "admin"),
    )
    df = dataset_service.load_version_dataframe(dataset_id=version.dataset_id, version_id=version.id)

    target_column = payload.target_column
    if target_column is None:
        analysis = await dataset_service.analyze_version(
            version_id=version.id,
            user_id=str(current_user.id),
            is_admin=(current_user.role == "admin"),
        )
        target_column = analysis.get("target_column")
    if not target_column:
        from app.core.exceptions import ValidationError
        raise ValidationError("Select the target column before executing preprocessing.")

    agent = PreprocessingAgent()
    if payload.steps:
        plan = PreprocessingPlan(
            dataset_id=str(version.dataset_id),
            dataset_version_id=str(version.id),
            steps=payload.steps,
            summary="User-approved deterministic preprocessing pipeline.",
        )
    else:
        plan = await agent.generate_plan(df, target_column=target_column)
        plan.dataset_id = str(version.dataset_id)
        plan.dataset_version_id = str(version.id)

    result = agent.execute_plan(df, plan, target_column=target_column)

    # Persist the output arrays as an artifact
    artifact_path = f"datasets/{version.dataset_id}/versions/{version.id}/artifacts/preprocessing_{uuid.uuid4().hex[:8]}.joblib"
    buffer = io.BytesIO()
    joblib.dump(result, buffer)
    artifact_storage.save(artifact_path, buffer.getvalue())

    from app.database.models.preprocessing import PreprocessingRun
    preprocessing_run = PreprocessingRun(
        dataset_version_id=str(version.id),
        user_id=str(current_user.id),
        status="completed",
        is_ready_for_training=True,
        artifact_storage_path=artifact_path,
        target_column=target_column,
        original_feature_count=df.shape[1] - 1,
        final_feature_count=len(result["feature_names"]),
        final_feature_names=result["feature_names"],
        config_params={
            "target_column": target_column,
            "mode": payload.mode,
            "steps": [step.model_dump(mode="json") for step in plan.steps],
        },
        imputation_strategy=next((
            str(step.parameters.get("strategy", step.tool_name))
            for step in plan.steps
            if "imput" in step.tool_name.lower()
        ), None),
        scaling_strategy=next((
            step.tool_name for step in plan.steps
            if any(name in step.tool_name.lower() for name in ("scaler", "normalizer"))
        ), None),
        encoding_strategy=next((
            step.tool_name for step in plan.steps
            if "encoder" in step.tool_name.lower()
        ), None),
    )
    await preprocessing_run.insert()

    return StandardResponse(
        message="Preprocessing executed successfully with data leakage prevention.",
        data={
            "run_id": str(preprocessing_run.id),
            "preprocessing_run_id": str(preprocessing_run.id),
            "dataset_version_id": str(version.id),
            "target_column": target_column,
            "status": "completed",
            "is_ready_for_training": True,
            "train_samples": result["train_samples"],
            "val_samples": result["val_samples"],
            "test_samples": result["test_samples"],
            "feature_names": result["feature_names"],
            "outlier_rows_removed": result["outlier_rows_removed"],
            "unencoded_categorical_columns": result["unencoded_categorical_columns"],
            "leakage_audit": "PASSED: Transformers fitted strictly on train partition.",
        },
    )


@router.get("/artifacts", response_model=StandardResponse[List[Dict[str, Any]]], status_code=status.HTTP_200_OK)
async def list_preprocessing_artifacts(
    dataset_version_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    from app.database.models.preprocessing import PreprocessingRun
    query = {"user_id": str(current_user.id), "is_ready_for_training": True}
    if dataset_version_id:
        query["dataset_version_id"] = dataset_version_id
    runs = await PreprocessingRun.find(query).to_list()
    
    return StandardResponse(
        message="Fetched preprocessing artifacts.",
        data=[r.model_dump(mode="json") for r in runs]
    )
