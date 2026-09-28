"""Feature selection and ranking API endpoints - Single Source of Truth for Models."""

from fastapi import APIRouter, Depends, status
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
