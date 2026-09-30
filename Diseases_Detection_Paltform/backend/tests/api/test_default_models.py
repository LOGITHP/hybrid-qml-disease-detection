"""API tests verifying system-wide default models accessible to all users."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_default_models_accessible_to_all_users(client: AsyncClient):
    """Ensure pre-trained default models are discoverable and usable by any registered user."""
    # 1. Register User 1
    await client.post(
        "/api/v1/auth/register",
        json={"email": "oncologist1@hospital.org", "password": "Password123!"},
    )
    login1 = await client.post(
        "/api/v1/auth/login",
        json={"email": "oncologist1@hospital.org", "password": "Password123!"},
    )
    token1 = login1.json()["access_token"]
    auth1 = {"Authorization": f"Bearer {token1}"}

    # 2. Register User 2
    await client.post(
        "/api/v1/auth/register",
        json={"email": "oncologist2@hospital.org", "password": "Password123!"},
    )
    login2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "oncologist2@hospital.org", "password": "Password123!"},
    )
    token2 = login2.json()["access_token"]
    auth2 = {"Authorization": f"Bearer {token2}"}

    # 3. Seed default models into registry
    seed_res = await client.post("/api/v1/models/seed-defaults", headers=auth1)
    assert seed_res.status_code == 200
    seeded_models = seed_res.json()["data"]
    assert len(seeded_models) >= 4

    default_model = seeded_models[0]
    default_model_id = default_model["id"]
    assert default_model["is_default"] is True

    # 4. User 1 can list default models
    list_res1 = await client.get("/api/v1/models", headers=auth1)
    assert list_res1.status_code == 200
    ids_user1 = [m["id"] for m in list_res1.json()]
    assert default_model_id in ids_user1

    # 5. User 2 can list default models
    list_res2 = await client.get("/api/v1/models", headers=auth2)
    assert list_res2.status_code == 200
    ids_user2 = [m["id"] for m in list_res2.json()]
    assert default_model_id in ids_user2

    # 6. User 2 can view details of default model
    get_res2 = await client.get(f"/api/v1/models/{default_model_id}", headers=auth2)
    assert get_res2.status_code == 200
    assert get_res2.json()["id"] == default_model_id
    assert get_res2.json()["is_default"] is True

    # 7. User 1 creates custom private model
    custom_res = await client.post(
        "/api/v1/models",
        json={"name": "User 1 Private Prototype", "model_type": "vqc"},
        headers=auth1,
    )
    assert custom_res.status_code == 201
    custom_id = custom_res.json()["data"]["id"]

    # 8. User 2 cannot access User 1's private model; the API hides its existence.
    forbidden_res = await client.get(f"/api/v1/models/{custom_id}", headers=auth2)
    assert forbidden_res.status_code == 404
