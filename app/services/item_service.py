"""Service layer for item-related business logic."""

from uuid import UUID

from app.api.v1.schemas.item import ItemCreate, ItemUpdate
from app.core.exceptions import AuthorizationError, NotFoundError
from app.persistence.models.item import Item
from app.persistence.uow.base import UnitOfWorkBase


class ItemService:
    """Service layer for item-related business logic."""

    def __init__(self, uow: UnitOfWorkBase) -> None:
        """Initialize the service with a unit of work instance."""
        self._uow = uow

    async def create_item(self, owner_id: UUID, data: ItemCreate) -> Item:
        """Create a new item owned by the specified user.

        Args:
            owner_id (UUID): The ID of the user who will own the item.
            data (ItemCreate): The details of the item to create.

        Returns:
            Item: The newly created item instance.
        """
        new_item = Item(
            title=data.title,
            description=data.description,
            price=data.price,
            owner_id=owner_id,
        )
        self._uow.items.add(new_item)
        await self._uow.commit()
        return new_item

    async def get_item(self, item_id: UUID, owner_id: UUID) -> Item:
        """Retrieve an item by its identifier, ensuring it belongs to the specified owner.

        Args:
            item_id (UUID): The unique identifier of the item to retrieve.
            owner_id (UUID): The ID of the user who must own the item.

        Returns:
            Item: The item instance with the specified ID.
        """
        item = await self._uow.items.find_by_id(item_id)

        if item is None:
            raise NotFoundError("Item", item_id)

        if item.owner_id != owner_id:
            raise AuthorizationError("retrieve", "Item")

        return item

    async def list_items(self, owner_id: UUID | None, skip: int = 0, limit: int = 20) -> list[Item]:
        """List items with optional owner filtering and pagination.

        Args:
            owner_id (UUID | None): The ID of the user who owns the items. If None, list all items.
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.

        Returns:
            list[Item]: A list of items matching the pagination criteria.
        """
        filters = {}
        if owner_id is not None:
            filters["owner_id"] = owner_id
        return await self._uow.items.find_all(
            skip=skip,
            limit=limit,
            **filters,
        )

    async def update_item(self, item_id: UUID, owner_id: UUID, data: ItemUpdate) -> Item:
        """Update an existing item with the provided fields.

        Args:
            item_id (UUID): The unique identifier of the item to update.
            owner_id (UUID): The ID of the user who owns the item.
            data (ItemUpdate): The fields to update on the item.

        Returns:
            Item: The updated item instance.

        Raises:
            NotFoundError: If the item does not exist.
            AuthorizationError: If the item exists but does not belong to the owner.
        """
        item = await self._uow.items.find_by_id(item_id)

        if item is None:
            raise NotFoundError("Item", item_id)

        if item.owner_id != owner_id:
            raise AuthorizationError("update", "Item")

        updated_item = await self._uow.items.update(item, **data.model_dump(exclude_unset=True))
        await self._uow.commit()
        return updated_item

    async def delete_item(self, item_id: UUID, owner_id: UUID) -> None:
        """Delete an item by its identifier.

        Args:
            item_id (UUID): The unique identifier of the item to delete.
            owner_id (UUID): The ID of the user who owns the item.

        Raises:
            NotFoundError: If the item does not exist.
            AuthorizationError: If the item exists but does not belong to the owner.
        """
        item = await self._uow.items.find_by_id(item_id)

        if item is None:
            raise NotFoundError("Item", item_id)

        if item.owner_id != owner_id:
            raise AuthorizationError("delete", "Item")

        await self._uow.items.delete(item_id)
        await self._uow.commit()
