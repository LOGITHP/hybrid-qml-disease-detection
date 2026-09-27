"""Unit tests for Argon2id hashing and JWT token security."""

import pytest
from app.core.exceptions import AuthenticationError, TokenExpiredError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_argon2id_password_hashing():
    """Verify that password hashing uses Argon2id and produces verifiable hashes."""
    pwd = "StrongBiomedicalPassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert "$argon2id$" in hashed
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_weak_password_rejected():
    """Ensure passwords under 8 characters are rejected."""
    with pytest.raises(ValueError):
        hash_password("short")


def test_jwt_access_token_generation_and_decoding():
    """Verify JWT access tokens contain proper claims and user ID."""
    user_id = "test-user-uuid-1234"
    role = "user"
    token = create_access_token(user_id=user_id, role=role)
    payload = decode_token(token, expected_type="access")

    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload


def test_jwt_refresh_token_generation_and_decoding():
    """Verify JWT refresh tokens can be decoded and validated."""
    user_id = "test-user-uuid-5678"
    token = create_refresh_token(user_id=user_id)
    payload = decode_token(token, expected_type="refresh")

    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


def test_invalid_jwt_rejected():
    """Verify tampered or invalid JWTs fail authentication."""
    with pytest.raises(AuthenticationError):
        decode_token("invalid.jwt.token", expected_type="access")
