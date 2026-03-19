"""Unit tests for ItemService business logic (mocked UoW)."""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.api.v1.schemas.item import ItemCreate
from app.core.exceptions import AuthorizationError, NotFoundError
from app.persistence.models.item import Item
from app.services.item_service import ItemService


class TestCreateItem:
    async def test_creates_item_for_owner(self, mock_uow: AsyncMock) -> None:
        mock_uow.commit = AsyncMock()

        service = ItemService(mock_uow)
        owner_id: UUID = uuid4()
        data = ItemCreate(title="Test Item", price=9.99)
        result = await service.create_item(owner_id, data)

        assert result.title == "Test Item"
        assert result.price == 9.99
        assert result.owner_id == owner_id
        mock_uow.items.add.assert_called_once()
        mock_uow.commit.assert_awaited_once()

    async def test_creates_item_with_description(self, mock_uow: AsyncMock) -> None:
        mock_uow.commit = AsyncMock()

        service = ItemService(mock_uow)
        data = ItemCreate(title="Item", description="A description", price=1.00)
        result = await service.create_item(uuid4(), data)

        assert result.description == "A description"


class TestGetItem:
    async def test_returns_item_for_correct_owner(self, mock_uow: AsyncMock) -> None:
        owner_id: UUID = uuid4()
        item = Item(id=uuid4(), title="Test", price=1.0, owner_id=owner_id)
        mock_uow.items.find_by_id = AsyncMock(return_value=item)

        service = ItemService(mock_uow)
        result = await service.get_item(item.id, owner_id)

        assert result == item

    async def test_raises_not_found_when_item_missing(self, mock_uow: AsyncMock) -> None:
        mock_uow.items.find_by_id = AsyncMock(return_value=None)

        service = ItemService(mock_uow)
        with pytest.raises(NotFoundError):
            await service.get_item(uuid4(), uuid4())

    async def test_raises_authorization_error_for_wrong_owner(self, mock_uow: AsyncMock) -> None:
        item = Item(id=uuid4(), title="Test", price=1.0, owner_id=uuid4())
        mock_uow.items.find_by_id = AsyncMock(return_value=item)

        service = ItemService(mock_uow)
        with pytest.raises(AuthorizationError):
            await service.get_item(item.id, uuid4())  # different owner


class TestListItems:
    async def test_returns_items_and_total(self, mock_uow: AsyncMock) -> None:
        owner_id: UUID = uuid4()
        items = [Item(title="A", price=1.0, owner_id=owner_id)]
        mock_uow.items.find_all = AsyncMock(return_value=items)
        mock_uow.items.count = AsyncMock(return_value=1)

        service = ItemService(mock_uow)
        result, total = await service.list_items(owner_id)

        assert result == items
        assert total == 1

    async def test_list_all_items_when_owner_is_none(self, mock_uow: AsyncMock) -> None:
        mock_uow.items.find_all = AsyncMock(return_value=[])
        mock_uow.items.count = AsyncMock(return_value=0)

        service = ItemService(mock_uow)
        result, total = await service.list_items(owner_id=None)

        assert result == []
        assert total == 0


class TestDeleteItem:
    async def test_deletes_item_for_owner(self, mock_uow: AsyncMock) -> None:
        owner_id: UUID = uuid4()
        item_id: UUID = uuid4()
        item = Item(id=item_id, title="Test", price=1.0, owner_id=owner_id)
        mock_uow.items.find_by_id = AsyncMock(return_value=item)
        mock_uow.items.delete = AsyncMock()
        mock_uow.commit = AsyncMock()

        service = ItemService(mock_uow)
        await service.delete_item(item_id, owner_id)

        mock_uow.items.delete.assert_awaited_once_with(item_id)

    async def test_raises_authorization_error_for_wrong_owner(self, mock_uow: AsyncMock) -> None:
        item = Item(id=uuid4(), title="Test", price=1.0, owner_id=uuid4())
        mock_uow.items.find_by_id = AsyncMock(return_value=item)

        service = ItemService(mock_uow)
        with pytest.raises(AuthorizationError):
            await service.delete_item(item.id, uuid4())


class TestUpdateItem:
    async def test_updates_item_for_owner(self, mock_uow: AsyncMock) -> None:
        from app.api.v1.schemas.item import ItemUpdate

        owner_id: UUID = uuid4()
        item_id: UUID = uuid4()
        item = Item(id=item_id, title="Old", price=1.0, owner_id=owner_id)
        updated = Item(id=item_id, title="New", price=2.0, owner_id=owner_id)
        mock_uow.items.find_by_id = AsyncMock(return_value=item)
        mock_uow.items.update = AsyncMock(return_value=updated)
        mock_uow.commit = AsyncMock()

        service = ItemService(mock_uow)
        result = await service.update_item(item_id, owner_id, ItemUpdate(title="New", price=2.0))

        assert result.title == "New"
        mock_uow.commit.assert_awaited_once()

    async def test_raises_not_found_when_item_missing(self, mock_uow: AsyncMock) -> None:
        from app.api.v1.schemas.item import ItemUpdate

        mock_uow.items.find_by_id = AsyncMock(return_value=None)

        service = ItemService(mock_uow)
        with pytest.raises(NotFoundError):
            await service.update_item(uuid4(), uuid4(), ItemUpdate(title="X", price=1.0))

    async def test_raises_authorization_error_for_wrong_owner(self, mock_uow: AsyncMock) -> None:
        from app.api.v1.schemas.item import ItemUpdate

        item = Item(id=uuid4(), title="Test", price=1.0, owner_id=uuid4())
        mock_uow.items.find_by_id = AsyncMock(return_value=item)

        service = ItemService(mock_uow)
        with pytest.raises(AuthorizationError):
            await service.update_item(item.id, uuid4(), ItemUpdate(title="X", price=1.0))


class TestDeleteItemNotFound:
    async def test_raises_not_found_when_item_missing(self, mock_uow: AsyncMock) -> None:
        mock_uow.items.find_by_id = AsyncMock(return_value=None)

        service = ItemService(mock_uow)
        with pytest.raises(NotFoundError):
            await service.delete_item(uuid4(), uuid4())


class TestListItemsFiltering:
    async def test_passes_owner_filter_to_repository(self, mock_uow: AsyncMock) -> None:
        owner_id: UUID = uuid4()
        mock_uow.items.find_all = AsyncMock(return_value=[])
        mock_uow.items.count = AsyncMock(return_value=0)

        service = ItemService(mock_uow)
        await service.list_items(owner_id, skip=5, limit=10)

        mock_uow.items.find_all.assert_awaited_once_with(skip=5, limit=10, owner_id=owner_id)
        mock_uow.items.count.assert_awaited_once_with(owner_id=owner_id)

    async def test_no_owner_filter_when_none(self, mock_uow: AsyncMock) -> None:
        mock_uow.items.find_all = AsyncMock(return_value=[])
        mock_uow.items.count = AsyncMock(return_value=0)

        service = ItemService(mock_uow)
        await service.list_items(owner_id=None)

        mock_uow.items.find_all.assert_awaited_once_with(skip=0, limit=20)
        mock_uow.items.count.assert_awaited_once_with()
