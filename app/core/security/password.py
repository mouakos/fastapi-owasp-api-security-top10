"""This module provides functions for hashing and verifying passwords using a strong password hashing algorithm with automatic salting and adaptive work factor.

It uses the `pwdlib` library to handle password hashing securely.
"""

from password_validator import PasswordValidator
from pwdlib import PasswordHash

# API2: Use a strong password hashing algorithm with automatic salting and adaptive work factor
password_hash = PasswordHash.recommended()

# Password complexity rules shared across hashing and seeding logic.
_complexity_schema = (
    PasswordValidator()
    .min(8)
    .max(128)
    .has()
    .uppercase()
    .has()
    .lowercase()
    .has()
    .digits()
    .has()
    .no()
    .spaces()
    .has()
    .symbols()
)


def validate_password_complexity(password: str) -> bool:
    """Return True if *password* satisfies the application complexity rules.

    Rules: 8-128 characters, at least one uppercase letter, one lowercase
    letter, one digit, one symbol, and no spaces.

    Args:
        password: The plaintext password to validate.

    Returns:
        bool: True if the password meets all complexity requirements.
    """
    result: bool = _complexity_schema.validate(password)
    return result


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
