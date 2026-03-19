"""Integration tests for SQLModelItemRepository against a real SQLite DB."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest

from app.core.security.password import hash_password
from app.persistence.models.item import Item
from app.persistence.models.user import User
from app.persistence.uow.sqlmodel_uow import SqlModelUnitOfWork


@pytest.fixture
async def owner(uow: SqlModelUnitOfWork) -> AsyncGenerator[User]:
    """Create and persist a user to act as item owner."""
    user = User(
        email=f"owner_{uuid4().hex[:8]}@example.com",
        username=f"owner_{uuid4().hex[:8]}",
        hashed_password=hash_password("Password1!"),
    )
    uow.users.add(user)
    await uow.commit()
    return user


class TestItemRepository:
    async def test_add_and_find_by_id(self, uow: SqlModelUnitOfWork, owner: User) -> None:
        item = Item(title="Test Item", price=9.99, owner_id=owner.id)
        uow.items.add(item)
        await uow.commit()

        found = await uow.items.find_by_id(item.id)
        assert found is not None
        assert found.title == "Test Item"

    async def test_find_by_id_returns_none_when_missing(self, uow: SqlModelUnitOfWork) -> None:
        found = await uow.items.find_by_id(uuid4())
        assert found is None

    async def test_find_all_filters_by_owner(self, uow: SqlModelUnitOfWork, owner: User) -> None:
        uow.items.add(Item(title="Item A", price=1.0, owner_id=owner.id))
        uow.items.add(Item(title="Item B", price=2.0, owner_id=owner.id))
        await uow.commit()

        items = await uow.items.find_all(skip=0, limit=10, owner_id=owner.id)
        assert all(i.owner_id == owner.id for i in items)

    async def test_count_by_owner(self, uow: SqlModelUnitOfWork, owner: User) -> None:
        uow.items.add(Item(title="Item X", price=5.0, owner_id=owner.id))
        await uow.commit()

        count = await uow.items.count(owner_id=owner.id)
        assert count >= 1

    async def test_delete_removes_item(self, uow: SqlModelUnitOfWork, owner: User) -> None:
        item = Item(title="To Delete", price=1.0, owner_id=owner.id)
        uow.items.add(item)
        await uow.commit()

        await uow.items.delete(item.id)
        await uow.commit()

        found = await uow.items.find_by_id(item.id)
        assert found is None

    async def test_find_one_by_owner(self, uow: SqlModelUnitOfWork, owner: User) -> None:
        item = Item(title="Find One", price=3.0, owner_id=owner.id)
        uow.items.add(item)
        await uow.commit()

        found = await uow.items.find_one(owner_id=owner.id)
        assert found is not None
        assert found.owner_id == owner.id

    async def test_find_one_returns_none_when_no_match(self, uow: SqlModelUnitOfWork) -> None:
        found = await uow.items.find_one(owner_id=uuid4())
        assert found is None

    async def test_delete_nonexistent_does_nothing(self, uow: SqlModelUnitOfWork) -> None:
        await uow.items.delete(uuid4())  # must not raise

    async def test_exists_returns_true(self, uow: SqlModelUnitOfWork, owner: User) -> None:
        item = Item(title="Exists", price=1.0, owner_id=owner.id)
        uow.items.add(item)
        await uow.commit()

        assert await uow.items.exists(item.id) is True

    async def test_exists_returns_false(self, uow: SqlModelUnitOfWork) -> None:
        assert await uow.items.exists(uuid4()) is False
