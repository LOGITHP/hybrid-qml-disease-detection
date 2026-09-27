"""API tests for health check and version endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """GET /api/v1/health should return ok status."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "hybrid-qml-backend"


@pytest.mark.asyncio
async def test_version_endpoint(client: AsyncClient):
    """GET /api/v1/version should return semantic version and environment."""
    response = await client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert "backend_version" in data
    assert "api_version" in data
    assert "environment" in data
