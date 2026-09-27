"""Artifact storage service implementing local filesystem persistence with path-traversal security."""

import os
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.exceptions import AppException
from app.interfaces.artifact import IArtifactStorage


class LocalArtifactStorage(IArtifactStorage):
    """Local filesystem artifact storage ensuring path containment and file integrity."""

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = Path(root_dir or settings.ARTIFACT_ROOT).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)
        # Ensure standard artifact subdirectories exist
        for subdir in ["datasets", "preprocessing", "models", "evaluations", "experiments", "reports"]:
            (self.root_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Resolve path and verify that it does not escape the artifact root directory."""
        # Sanitize path to prevent directory traversal
        clean_path = Path(relative_path.strip().lstrip("/\\"))
        resolved = (self.root_dir / clean_path).resolve()
        if not str(resolved).startswith(str(self.root_dir)):
            raise AppException(
                status_code=400,
                code="PATH_TRAVERSAL_DETECTED",
                message="Invalid artifact file path: directory traversal is strictly forbidden.",
            )
        return resolved

    def save(self, relative_path: str, data: bytes) -> str:
        """Persist bytes to target path. Returns storage URI."""
        target_path = self._resolve_safe_path(relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)
        return str(target_path)

    def load(self, relative_path: str) -> bytes:
        """Read bytes from target path."""
        target_path = self._resolve_safe_path(relative_path)
        if not target_path.exists() or not target_path.is_file():
            raise AppException(
                status_code=404,
                code="ARTIFACT_NOT_FOUND",
                message=f"Artifact not found at relative path '{relative_path}'.",
            )
        return target_path.read_bytes()

    def exists(self, relative_path: str) -> bool:
        """Check if an artifact exists."""
        target_path = self._resolve_safe_path(relative_path)
        return target_path.exists() and target_path.is_file()

    def delete(self, relative_path: str) -> bool:
        """Delete an artifact file."""
        target_path = self._resolve_safe_path(relative_path)
        if target_path.exists() and target_path.is_file():
            target_path.unlink()
            return True
        return False

    def get_uri(self, relative_path: str) -> str:
        """Return canonical URI for the artifact."""
        return str(self._resolve_safe_path(relative_path))


# Singleton default storage instance
artifact_storage = LocalArtifactStorage()
