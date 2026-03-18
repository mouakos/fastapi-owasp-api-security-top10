"""Unit tests for password hashing and verification."""

from app.core.security.password import hash_password, verify_password


def test_hash_password_returns_string() -> None:
    assert isinstance(hash_password("secret"), str)


def test_hash_is_not_plaintext() -> None:
    assert hash_password("secret") != "secret"


def test_two_hashes_of_same_password_differ() -> None:
    # Argon2 uses a random salt per hash
    assert hash_password("secret") != hash_password("secret")


def test_verify_correct_password_returns_true() -> None:
    hashed = hash_password("Password1!")
    assert verify_password("Password1!", hashed) is True


def test_verify_wrong_password_returns_false() -> None:
    hashed = hash_password("Password1!")
    assert verify_password("WrongPass1!", hashed) is False


def test_verify_empty_password_returns_false() -> None:
    hashed = hash_password("Password1!")
    assert verify_password("", hashed) is False
