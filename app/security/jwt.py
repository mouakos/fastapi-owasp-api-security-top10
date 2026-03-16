"""JWT utility functions for creating and decoding JSON Web Tokens.

This module provides functions to create JWT access tokens with customizable payloads
and expiration times, as well as functions to decode and verify JWT tokens, ensuring
they are valid and have not expired.
It uses the `PyJWT` library to handle JWT encoding and decoding securely.
"""

from datetime import timedelta
from typing import Any

import jwt

from app.core.config import settings
from app.utils.time import utcnow


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
    return jwt.encode(
        to_encode, settings.secret_key.get_secret_value(), algorithm=settings.algorithm
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode  and verify a JWT token.

    Args:
        token (str): The JWT token to decode.

    Returns:
        dict[str, Any] | None: The decoded token payload if valid, None otherwise.
    """
    return jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[settings.algorithm],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
