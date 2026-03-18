"""Integration tests for SQLModelUserRepository against a real SQLite DB."""

from uuid import uuid4

from app.core.security.password import hash_password
from app.persistence.models.user import User
from app.persistence.uow.sqlmodel_uow import SqlModelUnitOfWork


class TestUserRepository:
    async def test_add_and_find_by_email(self, uow: SqlModelUnitOfWork) -> None:
        user = User(
            email=f"user_{uuid4().hex[:8]}@example.com",
            username=f"user_{uuid4().hex[:8]}",
            hashed_password=hash_password("Password1!"),
        )
        uow.users.add(user)
        await uow.commit()

        found = await uow.users.find_by_email(user.email)
        assert found is not None
        assert found.email == user.email

    async def test_add_and_find_by_username(self, uow: SqlModelUnitOfWork) -> None:
        user = User(
            email=f"user_{uuid4().hex[:8]}@example.com",
            username=f"user_{uuid4().hex[:8]}",
            hashed_password=hash_password("Password1!"),
        )
        uow.users.add(user)
        await uow.commit()

        found = await uow.users.find_by_username(user.username)
        assert found is not None
        assert found.username == user.username

    async def test_find_by_email_returns_none_when_missing(self, uow: SqlModelUnitOfWork) -> None:
        found = await uow.users.find_by_email("nobody@example.com")
        assert found is None

    async def test_find_by_id(self, uow: SqlModelUnitOfWork) -> None:
        user = User(
            email=f"user_{uuid4().hex[:8]}@example.com",
            username=f"user_{uuid4().hex[:8]}",
            hashed_password=hash_password("Password1!"),
        )
        uow.users.add(user)
        await uow.commit()

        found = await uow.users.find_by_id(user.id)
        assert found is not None
        assert found.id == user.id

    async def test_find_by_id_returns_none_when_missing(self, uow: SqlModelUnitOfWork) -> None:
        found = await uow.users.find_by_id(uuid4())
        assert found is None
