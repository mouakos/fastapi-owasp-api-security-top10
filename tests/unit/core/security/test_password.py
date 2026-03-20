"""Unit tests for password hashing and verification."""

import pytest

from app.core.security.password import hash_password, validate_password_complexity, verify_password


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


class TestValidatePasswordComplexity:
    """Tests for the complexity rules: 8-128 chars, upper, lower, digit, symbol, no spaces."""

    def test_valid_password_returns_true(self) -> None:
        assert validate_password_complexity("Password1!") is True

    def test_too_short_returns_false(self) -> None:
        assert validate_password_complexity("Ab1!") is False

    def test_too_long_returns_false(self) -> None:
        assert validate_password_complexity("A1!" + "a" * 126) is False

    def test_exactly_min_length_returns_true(self) -> None:
        assert validate_password_complexity("Abcd12!@") is True

    def test_exactly_max_length_returns_true(self) -> None:
        assert validate_password_complexity("A1!" + "a" * 125) is True

    def test_missing_uppercase_returns_false(self) -> None:
        assert validate_password_complexity("password1!") is False

    def test_missing_lowercase_returns_false(self) -> None:
        assert validate_password_complexity("PASSWORD1!") is False

    def test_missing_digit_returns_false(self) -> None:
        assert validate_password_complexity("Password!!") is False

    def test_missing_symbol_returns_false(self) -> None:
        assert validate_password_complexity("Password12") is False

    def test_contains_space_returns_false(self) -> None:
        assert validate_password_complexity("Pass word1!") is False

    @pytest.mark.parametrize("symbol", ["!", "@", "#", "$", "%", "^", "&", "*"])
    def test_various_symbols_accepted(self, symbol: str) -> None:
        assert validate_password_complexity(f"Password1{symbol}") is True
