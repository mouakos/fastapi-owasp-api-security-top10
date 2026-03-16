"""This module provides functions for hashing and verifying passwords using a strong password hashing algorithm with automatic salting and adaptive work factor.

It uses the `pwdlib` library to handle password hashing securely.
"""

from pwdlib import PasswordHash

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
