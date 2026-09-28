"""Experiment tracking and CML vs QML comparative benchmark endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from app.core.dependencies import get_current_user, get_experiment_service
from app.database.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.experiment import ExperimentCreate, ExperimentResponse
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/experiments", tags=["Experiments & Comparison"])


class CompareRequest(BaseModel):
    training_run_ids: List[str]


@router.post("", response_model=StandardResponse[ExperimentResponse], status_code=status.HTTP_201_CREATED)
async def create_experiment(
    payload: ExperimentCreate,
    current_user: User = Depends(get_current_user),
    service: ExperimentService = Depends(get_experiment_service),
):
    """Create a research experiment container to group multi-model runs."""
    exp = await service.create_experiment(
        user_id=str(current_user.id),
        name=payload.name,
        description=payload.description,
        tags=payload.tags,
        dataset_id=payload.dataset_id,
        dataset_version_id=payload.dataset_version_id,
        dataset_name=payload.dataset_name,
        preprocessing_run_id=payload.preprocessing_run_id,
        feature_selection_run_id=payload.feature_selection_run_id,
        target_column=payload.target_column,
        selected_features=payload.selected_features,
    )
    return StandardResponse(
        message="Experiment container created.",
        data=ExperimentResponse.model_validate(exp),
    )


@router.get("", response_model=List[ExperimentResponse])
async def list_experiments(
    current_user: User = Depends(get_current_user),
    service: ExperimentService = Depends(get_experiment_service),
):
    experiments = await service.list_user_experiments(user_id=str(current_user.id))
    return [ExperimentResponse.model_validate(experiment) for experiment in experiments]


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    current_user: User = Depends(get_current_user),
    service: ExperimentService = Depends(get_experiment_service),
):
    experiment = await service.get_user_experiment(
        experiment_id=experiment_id,
        user_id=str(current_user.id),
        is_admin=(current_user.role == "admin"),
    )
    return ExperimentResponse.model_validate(experiment)


@router.post("/{experiment_id}/compare", response_model=StandardResponse[dict])
async def compare_runs(
    experiment_id: str,
    payload: CompareRequest,
    current_user: User = Depends(get_current_user),
    service: ExperimentService = Depends(get_experiment_service),
):
    """Aggregate CML and QML training runs into an end-to-end comparative benchmark and Markdown report."""
    report = await service.generate_comparative_report(
        user_id=str(current_user.id),
        experiment_id=experiment_id,
        training_run_ids=payload.training_run_ids,
    )
    return StandardResponse(
        message="Comparative benchmark report generated.",
        data=report,
    )
