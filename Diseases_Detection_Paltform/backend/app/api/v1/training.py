"""Model training orchestration endpoints."""

from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user, get_training_service
from app.database.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.training import TrainingRunCreate, TrainingRunResponse
from app.services.training_service import TrainingService

router = APIRouter(prefix="/training", tags=["Training"])


@router.post("", response_model=StandardResponse[TrainingRunResponse], status_code=status.HTTP_201_CREATED)
async def start_training_run(
    payload: TrainingRunCreate,
    current_user: User = Depends(get_current_user),
    service: TrainingService = Depends(get_training_service),
):
    """Train a built-in model against the uploaded dataset and saved pipeline runs."""
    run = await service.execute_training_run(
        user_id=str(current_user.id),
        model_id=payload.model_id,
        dataset_version_id=payload.dataset_version_id,
        feature_selection_run_id=payload.feature_selection_run_id,
        preprocessing_run_id=payload.preprocessing_run_id,
        hyperparameters=payload.hyperparameters,
        is_noisy_quantum=payload.is_noisy_quantum,
        noise_params=payload.noise_params,
    )
    return StandardResponse(
        message="Model training completed successfully.",
        data=TrainingRunResponse.model_validate(run),
    )


@router.get("/{run_id}", response_model=TrainingRunResponse)
async def get_training_status(
    run_id: str,
    current_user: User = Depends(get_current_user),
    service: TrainingService = Depends(get_training_service),
):
    """Retrieve training execution record and performance metrics."""
    run = await service.training_repo.get_by_id(run_id)
    if not run or (run.user_id != str(current_user.id) and current_user.role != "admin"):
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("TrainingRun", run_id)
    return TrainingRunResponse.model_validate(run)
