"""Authentication and authorization utilities for the API."""

from datetime import timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.config import settings
from app.utils.time import utcnow

# API2: Use a strong password hashing algorithm with automatic salting and adaptive work factor
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a plaintext password.

    Args:
        password (str): The plaintext password to hash.

    Returns:
        str: The hashed password.
    """
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed password.

    Args:
        plain_password (str): The plaintext password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the password is correct, False otherwise.
    """
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data (dict[str, Any]): The data to include in the token payload.
        expires_delta (timedelta | None, optional): The time until the token expires.

    Returns:
        str: The generated JWT access token.
    """
    to_encode = data.copy()
    expire = utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update(
        {
            "exp": expire,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        }
    )
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode  and verify a JWT token.

    Args:
        token (str): The JWT token to decode.

    Returns:
        dict[str, Any] | None: The decoded token payload if valid, None otherwise.
    """
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
