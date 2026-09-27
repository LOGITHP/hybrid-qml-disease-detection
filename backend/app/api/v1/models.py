"""Model registry API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user, get_model_service
from app.database.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.model import ModelCreate, ModelResponse, ModelVersionResponse
from app.services.model_service import ModelService

router = APIRouter(prefix="/models", tags=["Models"])


@router.post("", response_model=StandardResponse[ModelResponse], status_code=status.HTTP_201_CREATED)
async def register_model(
    payload: ModelCreate,
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """Register a new model archetype (svm_linear, svm_rbf, vqc)."""
    model = await service.register_model(
        user_id=current_user.id,
        name=payload.name,
        model_type=payload.model_type,
        description=payload.description,
    )
    return StandardResponse(
        message="Model archetype registered in registry.",
        data=ModelResponse.model_validate(model),
    )


@router.get("", response_model=List[ModelResponse])
async def list_models(
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """List registered models."""
    models = await service.list_user_models(user_id=current_user.id)
    return [ModelResponse.model_validate(m) for m in models]


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """Retrieve model archetype details."""
    model = await service.get_model(
        model_id=model_id,
        user_id=current_user.id,
        is_admin=(current_user.role == "admin"),
    )
    return ModelResponse.model_validate(model)


@router.get("/{model_id}/versions/{version_id}", response_model=ModelVersionResponse)
async def get_model_version(
    model_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """Fetch trained model version with evaluation metrics."""
    version = await service.get_model_version(
        version_id=version_id,
        user_id=current_user.id,
        is_admin=(current_user.role == "admin"),
    )
    return ModelVersionResponse.model_validate(version)
