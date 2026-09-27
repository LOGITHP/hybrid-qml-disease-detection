"""Health check and platform version endpoints."""

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health & Version"])


@router.get("/health")
async def health_check():
    """Health check endpoint to verify backend service readiness."""
    return {
        "status": "ok",
        "service": "hybrid-qml-backend",
    }


@router.get("/version")
async def version_info():
    """Expose application version, API version, and runtime environment."""
    return {
        "service": "hybrid-qml-backend",
        "backend_version": settings.VERSION,
        "api_version": settings.API_V1_PREFIX.lstrip("/"),
        "environment": settings.ENVIRONMENT,
    }
