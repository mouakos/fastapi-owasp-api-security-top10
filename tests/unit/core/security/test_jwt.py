"""Unit tests for JWT token creation and decoding."""

from datetime import timedelta

import jwt
import pytest

from app.core.security.jwt import create_access_token, decode_token


def test_create_access_token_returns_string() -> None:
    token = create_access_token({"sub": "some-user-id"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_valid_token_returns_payload() -> None:
    token = create_access_token({"sub": "user-123"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"


def test_decode_preserves_custom_claims() -> None:
    token = create_access_token({"sub": "user-123", "role": "admin"})
    payload = decode_token(token)
    assert payload["role"] == "admin"


def test_decode_token_contains_standard_claims() -> None:
    token = create_access_token({"sub": "user-123"})
    payload = decode_token(token)
    assert "exp" in payload
    assert "iss" in payload
    assert "aud" in payload


def test_create_token_with_custom_expiry() -> None:
    token = create_access_token({"sub": "user-123"}, expires_delta=timedelta(minutes=1))
    payload = decode_token(token)
    assert payload["sub"] == "user-123"


def test_decode_invalid_token_raises() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        decode_token("this.is.not.a.valid.token")


def test_decode_tampered_token_raises() -> None:
    token = create_access_token({"sub": "user-123"})
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(tampered)
