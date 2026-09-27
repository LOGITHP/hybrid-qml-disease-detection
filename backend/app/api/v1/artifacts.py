"""Artifact download and inspection endpoints."""

from fastapi import APIRouter, Depends, Response
from app.core.dependencies import get_current_user
from app.core.exceptions import ResourceNotFoundError
from app.database.models.user import User
from app.services.artifact_service import artifact_storage

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.get("/reports/{experiment_id}")
async def get_report_artifact(
    experiment_id: str,
    current_user: User = Depends(get_current_user),
):
    """Download Markdown benchmark report for an experiment."""
    report_rel_path = f"reports/experiments/{experiment_id}/benchmark_report.md"
    if not artifact_storage.exists(report_rel_path):
        raise ResourceNotFoundError("ReportArtifact", report_rel_path)

    data = artifact_storage.load(report_rel_path)
    return Response(content=data, media_type="text/markdown")
