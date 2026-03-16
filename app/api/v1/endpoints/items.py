"""API endpoints for item-related operations."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentActiveUserDependency, ItemServiceDependency
from app.api.v1.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.db.models.item import Item

router = APIRouter()


@router.get("/", response_model=list[ItemResponse], summary="List my items")
async def list_my_items(
    current_user: CurrentActiveUserDependency,
    item_service: ItemServiceDependency,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Item]:
    """Return paginated items that belong to the authenticated user."""
    return await item_service.list_items(current_user.id, skip=skip, limit=limit)


@router.get("/{item_id}", response_model=ItemResponse, summary="Get one of my items")
async def get_my_item(
    item_id: UUID,
    current_user: CurrentActiveUserDependency,
    item_service: ItemServiceDependency,
) -> Item:
    """Return one item owned by the authenticated user."""
    return await item_service.get_item(item_id=item_id, owner_id=current_user.id)  # type: ignore [arg-type]


@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new item",
)
async def create_my_item(
    data: ItemCreate,
    current_user: CurrentActiveUserDependency,
    item_service: ItemServiceDependency,
) -> Item:
    """Create a new item owned by the authenticated user."""
    return await item_service.create_item(owner_id=current_user.id, data=data)  # type: ignore [arg-type]


@router.patch("/{item_id}", response_model=ItemResponse, summary="Update one of my items")
async def update_my_item(
    item_id: UUID,
    data: ItemUpdate,
    current_user: CurrentActiveUserDependency,
    item_service: ItemServiceDependency,
) -> Item:
    """Partially update a user-owned item and return the updated record."""
    return await item_service.update_item(item_id=item_id, owner_id=current_user.id, data=data)  # type: ignore [arg-type]


@router.delete(
    "/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete one of my items"
)
async def delete_my_item(
    item_id: UUID,
    current_user: CurrentActiveUserDependency,
    item_service: ItemServiceDependency,
) -> None:
    """Delete an item owned by the authenticated user."""
    await item_service.delete_item(item_id=item_id, owner_id=current_user.id)  # type: ignore [arg-type]
