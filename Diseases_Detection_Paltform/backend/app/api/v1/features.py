"""Feature selection and ranking API endpoints - Single Source of Truth for Models."""

from fastapi import APIRouter, Depends, status
from typing import List, Dict, Any
from app.core.dependencies import get_current_user, get_dataset_service
from app.database.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.feature_selection import FeatureSelectionRequest, FeatureSelectionResponse
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/features", tags=["Feature Selection"])


@router.post("/select", response_model=StandardResponse[FeatureSelectionResponse], status_code=status.HTTP_201_CREATED)
async def select_features(
    payload: FeatureSelectionRequest,
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
):
    """Execute canonical feature selection (Single Source of Truth for SVM and VQC models)."""
    target = payload.target_column
    if target is None:
        analysis = await service.analyze_version(
            version_id=payload.dataset_version_id,
            user_id=str(current_user.id),
            is_admin=(current_user.role == "admin"),
        )
        target = analysis.get("target_column")
    if not target:
        from app.core.exceptions import ValidationError
        raise ValidationError("Select the target column before running feature selection.")

    fs_run = await service.execute_feature_selection(
        dataset_version_id=payload.dataset_version_id,
        user_id=str(current_user.id),
        target_column=target,
        ranking_method=payload.ranking_method,
        k_features=payload.k_features or 4,
        is_admin=(current_user.role == "admin"),
        selected_features=payload.selected_features,
    )
    return StandardResponse(
        message="Features ranked and canonical selection recorded.",
        data=FeatureSelectionResponse.model_validate(fs_run),
    )

@router.get("/runs", response_model=StandardResponse[List[Dict[str, Any]]], status_code=status.HTTP_200_OK)
async def list_feature_selection_runs(
    dataset_version_id: str | None = None,
    current_user: User = Depends(get_current_user)
):
    from app.database.models.feature_selection import FeatureSelectionRun
    query = {"user_id": str(current_user.id)}
    if dataset_version_id:
        query["dataset_version_id"] = dataset_version_id
    runs = await FeatureSelectionRun.find(query).to_list()
    return StandardResponse(
        message="Fetched feature selection runs.",
        data=[r.model_dump(mode="json") for r in runs]
    )

@router.delete("/runs/{run_id}", response_model=StandardResponse[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def delete_feature_selection_run(
    run_id: str,
    current_user: User = Depends(get_current_user)
):
    from app.database.models.feature_selection import FeatureSelectionRun
    from app.core.exceptions import ResourceNotFoundError
    from beanie import PydanticObjectId
    
    try:
        obj_id = PydanticObjectId(run_id)
    except Exception:
        raise ResourceNotFoundError("Feature selection run not found.")

    run = await FeatureSelectionRun.get(obj_id)
    if not run or (run.user_id != str(current_user.id) and current_user.role != "admin"):
        raise ResourceNotFoundError("Feature selection run not found.")

    await run.delete()
    return StandardResponse(
        message="Feature selection run deleted successfully.",
        data={"id": run_id}
    )

