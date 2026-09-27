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
    """Execute model training (SVM Linear, SVM RBF, or PennyLane VQC)."""
    run = await service.execute_training_run(
        user_id=current_user.id,
        model_id=payload.model_id,
        dataset_version_id=payload.dataset_version_id,
        feature_selection_run_id=payload.feature_selection_run_id,
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
    run = await service.training_repo.get_training_run(run_id, user_id=current_user.id)
    return TrainingRunResponse.model_validate(run)
