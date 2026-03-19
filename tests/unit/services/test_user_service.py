"""Unit tests for UserService business logic (mocked UoW)."""

from datetime import timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.schemas.user import UserAdminUpdate, UserCreate, UserUpdate
from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security.password import hash_password
from app.persistence.models.user import User
from app.services.user_service import UserService
from app.utils.time import utcnow


class TestCreateUser:
    async def test_creates_user_successfully(self, mock_uow: AsyncMock) -> None:
        mock_uow.users.find_by_email = AsyncMock(return_value=None)
        mock_uow.users.find_by_username = AsyncMock(return_value=None)
        mock_uow.commit = AsyncMock()

        service = UserService(mock_uow)
        data = UserCreate(email="new@example.com", username="newuser", password="Password1!")
        result = await service.create_user(data)

        assert result.email == "new@example.com"
        assert result.username == "newuser"
        mock_uow.users.add.assert_called_once()
        mock_uow.commit.assert_awaited_once()

    async def test_password_is_hashed_not_stored_plaintext(self, mock_uow: AsyncMock) -> None:
        mock_uow.users.find_by_email = AsyncMock(return_value=None)
        mock_uow.users.find_by_username = AsyncMock(return_value=None)
        mock_uow.commit = AsyncMock()

        service = UserService(mock_uow)
        data = UserCreate(email="new@example.com", username="newuser", password="Password1!")
        result = await service.create_user(data)

        assert result.hashed_password != "Password1!"

    async def test_raises_conflict_on_duplicate_email(self, mock_uow: AsyncMock) -> None:
        existing = User(email="dup@example.com", username="other", hashed_password="x")
        mock_uow.users.find_by_email = AsyncMock(return_value=existing)

        service = UserService(mock_uow)
        data = UserCreate(email="dup@example.com", username="newuser", password="Password1!")

        with pytest.raises(ConflictError):
            await service.create_user(data)

    async def test_raises_conflict_on_duplicate_username(self, mock_uow: AsyncMock) -> None:
        mock_uow.users.find_by_email = AsyncMock(return_value=None)
        existing = User(email="other@example.com", username="taken", hashed_password="x")
        mock_uow.users.find_by_username = AsyncMock(return_value=existing)

        service = UserService(mock_uow)
        data = UserCreate(email="new@example.com", username="taken", password="Password1!")

        with pytest.raises(ConflictError):
            await service.create_user(data)


class TestAuthenticateUser:
    async def test_raises_when_user_not_found(self, mock_uow: AsyncMock) -> None:
        mock_uow.users.find_by_email = AsyncMock(return_value=None)
        mock_uow.users.find_by_username = AsyncMock(return_value=None)

        service = UserService(mock_uow)
        with pytest.raises(AuthenticationError):
            await service.authenticate_user("ghost@example.com", "Password1!")

    async def test_raises_on_wrong_password(self, mock_uow: AsyncMock) -> None:
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("Password1!"),
        )
        mock_uow.users.find_by_email = AsyncMock(return_value=user)
        mock_uow.commit = AsyncMock()

        service = UserService(mock_uow)
        with pytest.raises(AuthenticationError):
            await service.authenticate_user("test@example.com", "WrongPass9!")

    async def test_increments_failed_attempts_on_wrong_password(self, mock_uow: AsyncMock) -> None:
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("Password1!"),
            failed_login_attempts=0,
        )
        mock_uow.users.find_by_email = AsyncMock(return_value=user)
        mock_uow.commit = AsyncMock()

        service = UserService(mock_uow)
        with pytest.raises(AuthenticationError):
            await service.authenticate_user("test@example.com", "WrongPass9!")

        assert user.failed_login_attempts == 1

    async def test_locks_account_after_max_failed_attempts(self, mock_uow: AsyncMock) -> None:
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("Password1!"),
            failed_login_attempts=settings.max_failed_login_attempts - 1,
        )
        mock_uow.users.find_by_email = AsyncMock(return_value=user)
        mock_uow.commit = AsyncMock()

        service = UserService(mock_uow)
        with pytest.raises(AuthenticationError):
            await service.authenticate_user("test@example.com", "WrongPass9!")

        assert user.locked_until is not None

    async def test_raises_when_account_is_locked(self, mock_uow: AsyncMock) -> None:
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("Password1!"),
            locked_until=utcnow() + timedelta(minutes=5),
        )
        mock_uow.users.find_by_email = AsyncMock(return_value=user)

        service = UserService(mock_uow)
        with pytest.raises(AuthenticationError):
            await service.authenticate_user("test@example.com", "Password1!")

    async def test_returns_token_on_successful_login(self, mock_uow: AsyncMock) -> None:
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("Password1!"),
        )
        mock_uow.users.find_by_email = AsyncMock(return_value=user)
        mock_uow.commit = AsyncMock()

        service = UserService(mock_uow)
        token = await service.authenticate_user("test@example.com", "Password1!")

        assert token.access_token
        assert isinstance(token.access_token, str)

    async def test_resets_failed_attempts_on_successful_login(self, mock_uow: AsyncMock) -> None:
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("Password1!"),
            failed_login_attempts=3,
        )
        mock_uow.users.find_by_email = AsyncMock(return_value=user)
        mock_uow.commit = AsyncMock()

        service = UserService(mock_uow)
        await service.authenticate_user("test@example.com", "Password1!")

        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    async def test_login_by_username(self, mock_uow: AsyncMock) -> None:
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("Password1!"),
        )
        mock_uow.users.find_by_email = AsyncMock(return_value=None)
        mock_uow.users.find_by_username = AsyncMock(return_value=user)
        mock_uow.commit = AsyncMock()

        service = UserService(mock_uow)
        token = await service.authenticate_user("testuser", "Password1!")

        assert token.access_token


class TestAuthenticateUserInactive:
    async def test_raises_when_account_is_inactive(self, mock_uow: AsyncMock) -> None:
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("Password1!"),
            is_active=False,
        )
        mock_uow.users.find_by_email = AsyncMock(return_value=user)

        service = UserService(mock_uow)
        with pytest.raises(AuthenticationError):
            await service.authenticate_user("test@example.com", "Password1!")


class TestGetUserById:
    async def test_returns_user_when_found(self, mock_uow: AsyncMock) -> None:
        user_id = uuid4()
        user = User(id=user_id, email="test@example.com", username="testuser", hashed_password="x")
        mock_uow.users.find_by_id = AsyncMock(return_value=user)

        service = UserService(mock_uow)
        result = await service.get_user_by_id(user_id)

        assert result == user

    async def test_raises_not_found_when_missing(self, mock_uow: AsyncMock) -> None:
        mock_uow.users.find_by_id = AsyncMock(return_value=None)

        service = UserService(mock_uow)
        with pytest.raises(NotFoundError):
            await service.get_user_by_id(uuid4())


class TestUpdateUser:
    async def test_updates_username_successfully(self, mock_uow: AsyncMock) -> None:
        user_id = uuid4()
        user = User(id=user_id, email="test@example.com", username="old", hashed_password="x")
        updated = User(
            id=user_id, email="test@example.com", username="newname", hashed_password="x"
        )
        mock_uow.users.find_by_id = AsyncMock(return_value=user)
        mock_uow.users.find_by_username = AsyncMock(return_value=None)
        mock_uow.users.update = AsyncMock(return_value=updated)
        mock_uow.commit = AsyncMock()

        service = UserService(mock_uow)
        result = await service.update_user(user_id, UserUpdate(username="newname"))

        assert result.username == "newname"
        mock_uow.commit.assert_awaited_once()

    async def test_raises_not_found_when_user_missing(self, mock_uow: AsyncMock) -> None:
        mock_uow.users.find_by_id = AsyncMock(return_value=None)

        service = UserService(mock_uow)
        with pytest.raises(NotFoundError):
            await service.update_user(uuid4(), UserUpdate(username="newname"))

    async def test_returns_unchanged_user_when_username_is_none(self, mock_uow: AsyncMock) -> None:
        user_id = uuid4()
        user = User(id=user_id, email="test@example.com", username="old", hashed_password="x")
        mock_uow.users.find_by_id = AsyncMock(return_value=user)

        service = UserService(mock_uow)
        result = await service.update_user(user_id, UserUpdate(username=None))

        assert result == user
        mock_uow.users.update.assert_not_called()

    async def test_raises_conflict_when_username_taken_by_other_user(
        self, mock_uow: AsyncMock
    ) -> None:
        user_id = uuid4()
        user = User(id=user_id, email="test@example.com", username="old", hashed_password="x")
        other = User(id=uuid4(), email="other@example.com", username="taken", hashed_password="x")
        mock_uow.users.find_by_id = AsyncMock(return_value=user)
        mock_uow.users.find_by_username = AsyncMock(return_value=other)

        service = UserService(mock_uow)
        with pytest.raises(ConflictError):
            await service.update_user(user_id, UserUpdate(username="taken"))


class TestListUsers:
    async def test_returns_users_and_total(self, mock_uow: AsyncMock) -> None:
        users = [User(email="a@example.com", username="a", hashed_password="x")]
        mock_uow.users.find_all = AsyncMock(return_value=users)
        mock_uow.users.count = AsyncMock(return_value=1)

        service = UserService(mock_uow)
        result, total = await service.list_users()

        assert result == users
        assert total == 1

    async def test_passes_skip_and_limit(self, mock_uow: AsyncMock) -> None:
        mock_uow.users.find_all = AsyncMock(return_value=[])
        mock_uow.users.count = AsyncMock(return_value=0)

        service = UserService(mock_uow)
        await service.list_users(skip=10, limit=5)

        mock_uow.users.find_all.assert_awaited_once_with(skip=10, limit=5)


class TestAdminUpdateUser:
    async def test_updates_user_fields(self, mock_uow: AsyncMock) -> None:
        user_id = uuid4()
        user = User(id=user_id, email="test@example.com", username="testuser", hashed_password="x")
        updated = User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            hashed_password="x",
            is_active=False,
        )
        mock_uow.users.find_by_id = AsyncMock(return_value=user)
        mock_uow.users.update = AsyncMock(return_value=updated)
        mock_uow.commit = AsyncMock()

        service = UserService(mock_uow)
        result = await service.admin_update_user(user_id, UserAdminUpdate(is_active=False))

        assert result == updated
        mock_uow.commit.assert_awaited_once()

    async def test_raises_not_found_when_user_missing(self, mock_uow: AsyncMock) -> None:
        mock_uow.users.find_by_id = AsyncMock(return_value=None)

        service = UserService(mock_uow)
        with pytest.raises(NotFoundError):
            await service.admin_update_user(uuid4(), UserAdminUpdate(is_active=False))
