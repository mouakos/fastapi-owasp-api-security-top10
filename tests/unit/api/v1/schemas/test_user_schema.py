"""Unit tests for UserCreate / UserUpdate Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from app.api.v1.schemas.user import UserCreate, UserUpdate


class TestUserCreate:
    def test_valid_payload_passes(self) -> None:
        user = UserCreate(email="user@example.com", username="validuser", password="Password1!")
        assert user.email == "user@example.com"

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", username="validuser", password="Password1!")

    def test_username_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", username="ab", password="Password1!")

    def test_username_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", username="a" * 31, password="Password1!")

    def test_username_with_invalid_chars_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", username="bad-name!", password="Password1!")

    def test_username_underscore_allowed(self) -> None:
        user = UserCreate(email="user@example.com", username="valid_user", password="Password1!")
        assert user.username == "valid_user"

    def test_password_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", username="validuser", password="Short1")

    def test_password_no_uppercase_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", username="validuser", password="nouppercase1!")

    def test_password_no_digit_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", username="validuser", password="NoDigitPass!")


class TestUserUpdate:
    def test_valid_username_update(self) -> None:
        update = UserUpdate(username="newname")
        assert update.username == "newname"

    def test_none_username_is_allowed(self) -> None:
        update = UserUpdate(username=None)
        assert update.username is None

    def test_empty_payload_is_allowed(self) -> None:
        update = UserUpdate()
        assert update.username is None

    def test_invalid_username_raises(self) -> None:
        import pytest
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            UserUpdate(username="bad name!")
