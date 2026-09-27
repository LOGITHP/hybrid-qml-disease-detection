"""Model registry service managing architectures, versions, and weights."""

from typing import List, Optional
from app.core.exceptions import CrossUserAccessError, ResourceNotFoundError, ValidationError
from app.database.models.model import Model, ModelConfig, ModelVersion
from app.repositories.model_repository import ModelRepository


class ModelService:
    """Service managing model registration, hyperparameter configurations, and trained versions."""

    def __init__(self, model_repo: ModelRepository):
        self.model_repo = model_repo

    async def register_model(self, user_id: str, name: str, model_type: str, description: Optional[str] = None) -> Model:
        """Register a new model archetype (svm_linear, svm_rbf, vqc)."""
        valid_types = {"svm_linear", "svm_rbf", "vqc"}
        if model_type not in valid_types:
            raise ValidationError(f"Invalid model_type '{model_type}'. Supported types: {list(valid_types)}")

        model = Model(user_id=user_id, name=name, model_type=model_type, description=description)
        return await self.model_repo.create(model)

    async def get_model(self, model_id: str, user_id: str, is_admin: bool = False) -> Model:
        """Fetch model by ID ensuring ownership check."""
        model = await self.model_repo.get_by_id(model_id)
        if not model:
            raise ResourceNotFoundError(resource_type="Model", resource_id=model_id)
        if not is_admin and model.user_id != user_id:
            raise CrossUserAccessError(resource_type="Model", resource_id=model_id)
        return model

    async def list_user_models(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Model]:
        """List models created by user."""
        return await self.model_repo.list_by_user(user_id, skip=skip, limit=limit)

    async def get_model_version(self, version_id: str, user_id: str, is_admin: bool = False) -> ModelVersion:
        """Fetch specific trained model version."""
        version = await self.model_repo.get_version_by_id(version_id)
        if not version:
            raise ResourceNotFoundError(resource_type="ModelVersion", resource_id=version_id)
        if not is_admin and version.user_id != user_id:
            raise CrossUserAccessError(resource_type="ModelVersion", resource_id=version_id)
        return version
