"""API tests for user authentication and authorization."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_full_lifecycle(client: AsyncClient):
    """Test full registration, login, profile retrieval, and token refresh cycle."""
    email = "scientist@qmlplatform.org"
    password = "SecurePassword123!"

    # 1. Register new user
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Dr. Quantum"},
    )
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()["data"]
    assert user_data["email"] == email
    assert user_data["role"] == "user"

    # 2. Duplicate registration rejected
    dup_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert dup_resp.status_code == 409

    # 3. Weak password rejected
    weak_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "other@qml.org", "password": "short"},
    )
    assert weak_resp.status_code == 422

    # 4. Successful login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 5. Incorrect password rejected
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword123!"},
    )
    assert bad_login.status_code == 401

    # 6. /me endpoint with Bearer token
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == email

    # 7. /me endpoint without token rejected
    unauth_resp = await client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401

    # 8. Token refresh
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()
