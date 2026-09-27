"""Model registry API endpoints with system-wide default models and multi-model comparative evaluation."""

from typing import List
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user, get_model_service
from app.database.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.evaluation import ComprehensiveComparisonResponse, ModelComparisonRequest
from app.schemas.model import ModelCreate, ModelResponse, ModelVersionResponse
from app.services.model_service import ModelService

router = APIRouter(prefix="/models", tags=["Models & Comparative Benchmarks"])


@router.post("", response_model=StandardResponse[ModelResponse], status_code=status.HTTP_201_CREATED)
async def register_model(
    payload: ModelCreate,
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """Register a new user-custom model archetype."""
    model = await service.register_model(
        user_id=current_user.id,
        name=payload.name,
        model_type=payload.model_type,
        description=payload.description,
        is_default=False,
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
    """List models accessible to the user (their own models + system-wide default pre-trained models)."""
    models = await service.list_user_models(user_id=current_user.id)
    return [ModelResponse.model_validate(m) for m in models]


@router.get("/defaults", response_model=List[ModelResponse])
async def list_default_models(
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """List all pre-trained system models available to every user by default."""
    models = await service.model_repo.list_defaults()
    return [ModelResponse.model_validate(m) for m in models]


@router.post("/seed-defaults", response_model=StandardResponse[List[ModelResponse]])
async def seed_defaults(
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """Seed or update all pre-trained repository models into the system registry."""
    seeded = await service.seed_default_models()
    return StandardResponse(
        message=f"Seeded {len(seeded)} pre-trained models into the platform.",
        data=[ModelResponse.model_validate(m) for m in seeded],
    )


@router.post("/compare", response_model=ComprehensiveComparisonResponse)
async def compare_models(
    payload: ModelComparisonRequest,
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """Compare two or more selected models across ALL evaluation metrics.
    
    Evaluates:
    - Overall Accuracy
    - Balanced Accuracy
    - Sensitivity (Recall)
    - Specificity
    - Precision
    - F1-Score
    - ROC-AUC
    - Confusion Matrix (TP, TN, FP, FN)
    - Training Duration
    - Quantum Qubit/Noise Specifications (if VQC)
    - Category Winners and CML vs QML Advantage Analysis
    """
    return await service.compare_selected_models(
        user_id=current_user.id,
        model_ids=payload.model_ids,
        model_version_ids=payload.model_version_ids,
        is_admin=(current_user.role == "admin"),
    )


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
