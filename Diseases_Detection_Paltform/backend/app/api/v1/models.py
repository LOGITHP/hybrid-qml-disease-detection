"""Model registry API endpoints with system-wide default models and multi-model comparative evaluation."""

from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from io import BytesIO
from app.core.dependencies import get_current_user, get_model_service
from app.database.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.evaluation import ComprehensiveComparisonResponse, ModelComparisonRequest
from app.schemas.model import ModelCreate, ModelResponse
from app.services.model_service import ModelService
from app.services.artifact_service import artifact_storage
from app.core.exceptions import ResourceNotFoundError, ValidationError

router = APIRouter(prefix="/models", tags=["Models & Comparative Benchmarks"])


@router.post("", response_model=StandardResponse[ModelResponse], status_code=status.HTTP_201_CREATED)
async def register_model(
    payload: ModelCreate,
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """Register a new user-custom model archetype."""
    model = await service.register_model(
        user_id=str(current_user.id),
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
    """List the user's trained models and shared built-in model templates."""
    models = await service.list_user_models(user_id=str(current_user.id))
    return [ModelResponse.model_validate(m) for m in models]


@router.get("/defaults", response_model=List[ModelResponse])
async def list_default_models(
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """List built-in system model templates that are fitted to an uploaded dataset during training."""
    await service.seed_default_models()
    models = await service.model_repo.list_defaults()
    return [ModelResponse.model_validate(m) for m in models]


@router.post("/seed-defaults", response_model=StandardResponse[List[ModelResponse]])
async def seed_defaults(
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """Seed the built-in model templates into the system registry."""
    seeded = await service.seed_default_models()
    return StandardResponse(
        message=f"Seeded {len(seeded)} built-in model templates into the platform.",
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
        user_id=str(current_user.id),
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
        user_id=str(current_user.id),
        is_admin=(current_user.role == "admin"),
    )
    return ModelResponse.model_validate(model)


@router.get("/{model_id}/artifact")
async def download_model_artifact(
    model_id: str,
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """Download the serialized artifact for an owned trained model."""
    model = await service.get_model(model_id, str(current_user.id), is_admin=(current_user.role == "admin"))
    if model.status not in {"trained", "candidate"}:
        raise ValidationError("Only trained or validation-candidate models have downloadable artifacts.")
    path = f"models/{model.id}/model.joblib"
    if not artifact_storage.exists(path):
        raise ResourceNotFoundError("ModelArtifact", path)
    payload = artifact_storage.load(path)
    return StreamingResponse(
        BytesIO(payload),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="model-{model.id}.joblib"'},
    )


@router.delete("/{model_id}", response_model=StandardResponse[ModelResponse])
async def delete_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    service: ModelService = Depends(get_model_service),
):
    """Soft-delete a user's model and remove only its serialized model artifact."""
    model = await service.get_model(model_id, str(current_user.id), is_admin=(current_user.role == "admin"))
    if model.is_default or model.user_id != str(current_user.id):
        raise ValidationError("Shared system models cannot be deleted.")
    artifact_storage.delete(f"models/{model.id}/model.joblib")
    model.status = "deleted"
    await service.model_repo.update(model)
    return StandardResponse(message="Model removed from the model zoo. Its dataset, training, and evaluation lineage remains recorded.", data=ModelResponse.model_validate(model))



