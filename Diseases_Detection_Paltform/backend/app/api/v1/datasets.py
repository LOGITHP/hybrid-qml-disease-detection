"""Dataset upload, management, and profiling endpoints."""

from typing import List
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from app.core.dependencies import get_current_user, get_dataset_service
from app.database.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.dataset import DatasetCreate, DatasetResponse, DatasetVersionResponse
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("", response_model=StandardResponse[DatasetResponse], status_code=status.HTTP_201_CREATED)
async def create_dataset(
    payload: DatasetCreate,
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
):
    """Register a new biomedical dataset container."""
    dataset = await service.create_dataset(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    return StandardResponse(
        message="Dataset created successfully.",
        data=DatasetResponse.model_validate(dataset),
    )


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
):
    """List datasets owned by the authenticated user."""
    datasets = await service.list_user_datasets(user_id=current_user.id)
    return [DatasetResponse.model_validate(d) for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
):
    """Retrieve metadata for a specific dataset."""
    dataset = await service.get_dataset(
        dataset_id=dataset_id,
        user_id=current_user.id,
        is_admin=(current_user.role == "admin"),
    )
    return DatasetResponse.model_validate(dataset)


@router.post("/{dataset_id}/versions", response_model=StandardResponse[DatasetVersionResponse], status_code=status.HTTP_201_CREATED)
async def upload_dataset_version(
    dataset_id: str,
    file: UploadFile = File(...),
    version_tag: str = Form("v1.0"),
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
):
    """Upload an immutable CSV version for a dataset."""
    file_bytes = await file.read()
    version = await service.upload_version(
        dataset_id=dataset_id,
        user_id=current_user.id,
        file_bytes=file_bytes,
        filename=file.filename or "dataset.csv",
        version_tag=version_tag,
        is_admin=(current_user.role == "admin"),
    )
    return StandardResponse(
        message="Dataset version uploaded and validated.",
        data=DatasetVersionResponse.model_validate(version),
    )


@router.get("/{dataset_id}/versions/{version_id}/analysis")
async def analyze_dataset_version(
    dataset_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
):
    """Compute privacy-preserving statistical summary without leaking patient data."""
    return await service.analyze_version(
        version_id=version_id,
        user_id=current_user.id,
        is_admin=(current_user.role == "admin"),
    )
