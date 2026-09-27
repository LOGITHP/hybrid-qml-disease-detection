"""FastAPI route dependencies for authentication, authorization, and service injection."""

from typing import Annotated, Callable
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_token
from app.database.models.user import User
from app.database.session import get_db
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.repositories.model_repository import ModelRepository
from app.repositories.training_repository import TrainingRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.dataset_service import DatasetService
from app.services.experiment_service import ExperimentService
from app.services.model_service import ModelService
from app.services.training_service import TrainingService
from app.services.user_service import UserService


async def get_current_user(
    authorization: Annotated[str, Header()] = "",
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency extracting and validating the Bearer access token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header. Expected 'Bearer <token>'.")

    token = authorization.split(" ")[1].strip()
    payload = decode_token(token, expected_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token payload missing subject identifier.")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationError("Authenticated user no longer exists.")

    if not user.is_active:
        raise AuthenticationError("User account is deactivated.")

    return user


def require_role(required_role: str) -> Callable:
    """Role-based authorization dependency enforcing admin or designated permissions."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role and current_user.role != "admin":
            raise PermissionDeniedError(
                f"Action requires role '{required_role}'. Your current role is '{current_user.role}'."
            )
        return current_user

    return role_checker


# Service factories for dependency injection
def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


def get_dataset_service(db: AsyncSession = Depends(get_db)) -> DatasetService:
    return DatasetService(DatasetRepository(db))


def get_model_service(db: AsyncSession = Depends(get_db)) -> ModelService:
    return ModelService(ModelRepository(db))


def get_training_service(db: AsyncSession = Depends(get_db)) -> TrainingService:
    return TrainingService(
        training_repo=TrainingRepository(db),
        model_repo=ModelRepository(db),
        dataset_repo=DatasetRepository(db),
    )


def get_experiment_service(db: AsyncSession = Depends(get_db)) -> ExperimentService:
    return ExperimentService(
        experiment_repo=ExperimentRepository(db),
        training_repo=TrainingRepository(db),
        model_repo=ModelRepository(db),
        dataset_repo=DatasetRepository(db),
    )
