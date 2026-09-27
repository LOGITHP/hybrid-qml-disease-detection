"""Artifact storage abstraction interface."""

from abc import ABC, abstractmethod
import hashlib
from typing import Optional


class IArtifactStorage(ABC):
    """Abstract interface for artifact file storage (Local filesystem or S3/MinIO)."""

    @abstractmethod
    def save(self, relative_path: str, data: bytes) -> str:
        """Store binary data at the relative path. Returns absolute or storage URI."""
        pass

    @abstractmethod
    def load(self, relative_path: str) -> bytes:
        """Retrieve binary data from the relative path."""
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Check whether an artifact exists at the relative path."""
        pass

    @abstractmethod
    def delete(self, relative_path: str) -> bool:
        """Delete an artifact if it exists."""
        pass

    @abstractmethod
    def get_uri(self, relative_path: str) -> str:
        """Get canonical storage URI or local file path."""
        pass

    @staticmethod
    def compute_checksum(data: bytes) -> str:
        """Compute SHA-256 hex digest for provenance and data integrity."""
        return hashlib.sha256(data).hexdigest()
