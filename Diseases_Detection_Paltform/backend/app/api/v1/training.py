"""Model training orchestration endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status, BackgroundTasks
from app.core.dependencies import get_current_user, get_training_service
from app.database.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.training import TrainingRunCreate, TrainingRunResponse
from app.database.models.training import TrainingRun
from app.services.training_service import TrainingService

router = APIRouter(prefix="/training", tags=["Training"])


@router.get("", response_model=List[TrainingRunResponse])
async def list_training_runs(
    current_user: User = Depends(get_current_user),
    service: TrainingService = Depends(get_training_service),
):
    """List the authenticated user's training runs, newest first."""
    runs = await service.training_repo.list_by_user(user_id=str(current_user.id))
    return [TrainingRunResponse.model_validate(run) for run in runs]


@router.post("", response_model=StandardResponse[TrainingRunResponse], status_code=status.HTTP_201_CREATED)
async def start_training_run(
    payload: TrainingRunCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: TrainingService = Depends(get_training_service),
):
    run = await service.training_repo.create(TrainingRun(
        user_id=str(current_user.id),
        model_id=payload.model_id,
        custom_name=payload.custom_name,
        dataset_version_id=payload.dataset_version_id,
        feature_selection_run_id=payload.feature_selection_run_id,
        preprocessing_run_id=payload.preprocessing_run_id,
        status="pending"
    ))
    
    async def training_task_wrapper():
        import logging
        try:
            await service.execute_training_run(
                user_id=str(current_user.id),
                model_id=payload.model_id,
                dataset_version_id=payload.dataset_version_id,
                feature_selection_run_id=payload.feature_selection_run_id,
                preprocessing_run_id=payload.preprocessing_run_id,
                hyperparameters=payload.hyperparameters,
                is_noisy_quantum=payload.is_noisy_quantum,
                noise_params=payload.noise_params,
                custom_name=payload.custom_name,
                run_id=str(run.id)
            )
        except Exception as e:
            logging.error(f"Background training task failed: {e}", exc_info=True)
            failed_run = await service.training_repo.get_by_id(str(run.id))
            if failed_run:
                failed_run.status = "failed"
                failed_run.error_message = str(e)
                await service.training_repo.update(failed_run)

    background_tasks.add_task(training_task_wrapper)
    
    return StandardResponse(
        message="Model training started in background.",
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

@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_training_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    service: TrainingService = Depends(get_training_service),
):
    """Cancel or delete a training run."""
    run = await service.training_repo.get_by_id(run_id)
    if not run or (run.user_id != str(current_user.id) and current_user.role != "admin"):
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("TrainingRun", run_id)
    
    # Mark as cancelled in DB
    run.status = "cancelled"
    await service.training_repo.update(run)
    return None

@router.post("/{run_id}/pause", response_model=TrainingRunResponse)
async def pause_training_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    service: TrainingService = Depends(get_training_service),
):
    """Pause a training run (DB state update only)."""
    run = await service.training_repo.get_by_id(run_id)
    if not run or (run.user_id != str(current_user.id) and current_user.role != "admin"):
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("TrainingRun", run_id)
    
    run.status = "paused"
    await service.training_repo.update(run)
    return TrainingRunResponse.model_validate(run)
