"""Unit tests for local artifact storage abstraction and security."""

import pytest
from app.core.exceptions import AppException
from app.services.artifact_service import LocalArtifactStorage


def test_artifact_lifecycle(tmp_path):
    """Test saving, loading, checking existence, and deleting artifacts."""
    storage = LocalArtifactStorage(root_dir=str(tmp_path))
    test_data = b"Sample biomedical CSV content: age,gender,lung_cancer\n45,1,0"

    rel_path = "datasets/test_dataset/original.csv"
    uri = storage.save(rel_path, test_data)

    assert storage.exists(rel_path) is True
    loaded = storage.load(rel_path)
    assert loaded == test_data

    # Checksum verification
    checksum = storage.compute_checksum(test_data)
    assert len(checksum) == 64

    # Delete
    deleted = storage.delete(rel_path)
    assert deleted is True
    assert storage.exists(rel_path) is False


def test_path_traversal_prevention(tmp_path):
    """Ensure directory traversal attacks are caught and rejected."""
    storage = LocalArtifactStorage(root_dir=str(tmp_path))
    with pytest.raises(AppException) as exc:
        storage.save("../../etc/passwd", b"malicious")
    assert exc.value.code == "PATH_TRAVERSAL_DETECTED"
