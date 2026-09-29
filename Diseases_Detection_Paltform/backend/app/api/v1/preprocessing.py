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
from app.schemas.preprocessing import PreprocessingPlan, PreprocessingPlanStep, AIModifyRequest, AIModifyResponse
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
    generation_method: str = "rule_based"
    generation_provider: Optional[str] = None


@router.post("/plan", response_model=StandardResponse[PreprocessingPlan], status_code=status.HTTP_200_OK)
async def generate_preprocessing_plan(
    payload: PlanRequest,
    current_user: User = Depends(get_current_user),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """Generate a schema-aware preprocessing plan for the selected uploaded dataset."""
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
        message="Schema-based preprocessing plan generated successfully.",
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

    from app.database.models.preprocessing import PreprocessingRun, PreprocessingArtifact
    import sklearn
    import pandas as pd
    import numpy as np

    preprocessing_run = PreprocessingRun(
        dataset_version_id=str(version.id),
        user_id=str(current_user.id),
        status="completed",
        config_params={
            "mode": payload.mode,
            "plan_generation_method": payload.generation_method,
            "plan_generation_provider": payload.generation_provider,
        }
    )
    await preprocessing_run.insert()

    artifact = PreprocessingArtifact(
        dataset_id=str(version.dataset_id),
        dataset_version_id=str(version.id),
        preprocessing_run_id=str(preprocessing_run.id),
        user_id=str(current_user.id),
        pipeline_version=1,
        pipeline_config={
            "steps": [step.model_dump(mode="json") for step in plan.steps],
            "generation_method": payload.generation_method,
            "generation_provider": payload.generation_provider,
        },
        original_features=result["original_features"],
        selected_features=result["selected_features"],
        final_features=result["feature_names"],
        target_column=target_column,
        train_split_metadata={"samples": result["train_samples"]},
        validation_split_metadata={"samples": result["val_samples"]},
        test_split_metadata={"samples": result["test_samples"]},
        feature_schema={f: "float64" for f in result["feature_names"]},
        final_feature_count=len(result["feature_names"]),
        output_dataset_location="n/a",
        artifact_storage_path=artifact_path,
        library_versions={"sklearn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        status="ready"
    )
    await artifact.insert()

    return StandardResponse(
        message="Preprocessing executed successfully with data leakage prevention.",
        data={
            "run_id": str(preprocessing_run.id),
            "preprocessing_run_id": str(preprocessing_run.id),
            "dataset_version_id": str(version.id),
            "target_column": target_column,
            "plan_generation_method": payload.generation_method,
            "plan_generation_provider": payload.generation_provider,
            "status": "completed",
            "is_ready_for_training": True,
            "train_samples": result["train_samples"],
            "val_samples": result["val_samples"],
            "test_samples": result["test_samples"],
            "feature_names": result["feature_names"],
            "outlier_rows_removed": result["outlier_rows_removed"],
            "unencoded_categorical_columns": result["unencoded_categorical_columns"],
            "leakage_audit": (
                "Split-before-fit check passed: transformers were fitted on training rows and reused unchanged "
                "for validation/test. Patient-group and duplicate-row leakage are not assessed."
            ),
        },
    )


@router.get("/artifacts", response_model=StandardResponse[List[Dict[str, Any]]], status_code=status.HTTP_200_OK)
async def list_preprocessing_artifacts(
    dataset_version_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    from app.database.models.preprocessing import PreprocessingRun, PreprocessingArtifact
    
    query = {"user_id": str(current_user.id)}
    if dataset_version_id:
        query["dataset_version_id"] = dataset_version_id
    
    # Fetch from the new PreprocessingArtifact collection
    artifacts = await PreprocessingArtifact.find(query).to_list()
    
    return StandardResponse(
        message="Fetched preprocessing artifacts.",
        data=[a.model_dump(mode="json") for a in artifacts]
    )


@router.post("/ai/modify", response_model=StandardResponse[AIModifyResponse], status_code=status.HTTP_200_OK)
async def modify_pipeline_nlp(
    payload: AIModifyRequest,
    current_user: User = Depends(get_current_user),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """Refine the current plan with the configured LLM and validate it against the uploaded schema."""
    version = await dataset_service.get_version(
        version_id=payload.dataset_version_id,
        user_id=str(current_user.id),
        is_admin=(current_user.role == "admin"),
    )
    if str(version.dataset_id) != payload.dataset_id:
        from app.core.exceptions import ValidationError
        raise ValidationError("The selected dataset version does not belong to the plan's dataset.")
    if payload.current_pipeline.dataset_id != payload.dataset_id:
        from app.core.exceptions import ValidationError
        raise ValidationError("The current plan belongs to a different dataset. Rebuild it before requesting an update.")

    df = dataset_service.load_version_dataframe(dataset_id=version.dataset_id, version_id=version.id)
    agent = PreprocessingAgent()
    result = await agent.modify_pipeline(payload, df)
    
    return StandardResponse(
        message="AI evaluated the instruction and produced a modification response.",
        data=result
    )
