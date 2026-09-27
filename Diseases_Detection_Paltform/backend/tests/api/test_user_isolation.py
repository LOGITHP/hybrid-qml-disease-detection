"""API tests verifying multi-user isolation and resource ownership security."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cross_user_resource_access_denied(client: AsyncClient):
    """User B must be strictly forbidden from accessing User A's dataset."""
    # 1. Register and login User A
    await client.post(
        "/api/v1/auth/register",
        json={"email": "usera@hospital.org", "password": "Password123!"},
    )
    res_a = await client.post(
        "/api/v1/auth/login",
        json={"email": "usera@hospital.org", "password": "Password123!"},
    )
    token_a = res_a.json()["access_token"]

    # 2. Register and login User B
    await client.post(
        "/api/v1/auth/register",
        json={"email": "userb@clinic.org", "password": "Password123!"},
    )
    res_b = await client.post(
        "/api/v1/auth/login",
        json={"email": "userb@clinic.org", "password": "Password123!"},
    )
    token_b = res_b.json()["access_token"]

    # 3. User A creates a dataset
    create_resp = await client.post(
        "/api/v1/datasets",
        json={"name": "Confidential Lung Cancer Study A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_resp.status_code == 201
    dataset_id = create_resp.json()["data"]["id"]

    # 4. User B attempts to access User A's dataset
    forbidden_resp = await client.get(
        f"/api/v1/datasets/{dataset_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    # Must deny access with 403 Forbidden
    assert forbidden_resp.status_code == 403
    error_code = forbidden_resp.json()["error"]["code"]
    assert error_code == "PERMISSION_DENIED"
