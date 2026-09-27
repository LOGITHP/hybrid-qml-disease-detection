"""Main API v1 router bundling all domain routers."""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.features import router as features_router
from app.api.v1.models import router as models_router
from app.api.v1.training import router as training_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.quantum import router as quantum_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.artifacts import router as artifacts_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(features_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(training_router)
api_v1_router.include_router(predictions_router)
api_v1_router.include_router(quantum_router)
api_v1_router.include_router(experiments_router)
api_v1_router.include_router(artifacts_router)
