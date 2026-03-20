"""API endpoints for item-related operations."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUserDependency, ItemServiceDependency, PaginationDependency
from app.api.v1.schemas.common import Page
from app.api.v1.schemas.item import (
    ExternalItemPayload,
    ItemCreate,
    ItemImportRequest,
    ItemResponse,
    ItemUpdate,
)
from app.persistence.models.item import Item
from app.utils.http_client import fetch_external
from app.utils.ssrf import validate_ssrf

router = APIRouter()


# ---------------------------------------------------------------------------
# API1: Every endpoint scopes reads and writes to the authenticated user's own
#       items; owner enforcement is applied in ItemService for every operation.
# API4: The list endpoint uses PaginationDependency to cap page size at 100.
# ---------------------------------------------------------------------------


@router.get("/", response_model=Page[ItemResponse], summary="List my items")
async def list_my_items(
    current_user: CurrentUserDependency,
    item_service: ItemServiceDependency,
    pagination: PaginationDependency,
) -> Page[Item]:
    """Return paginated items that belong to the authenticated user."""
    items, total = await item_service.list_items(
        current_user.id, skip=pagination.skip, limit=pagination.size
    )
    return Page(items=items, total=total, page=pagination.page, size=pagination.size)


@router.get("/{item_id}", response_model=ItemResponse, summary="Get one of my items")
async def get_my_item(
    item_id: UUID,
    current_user: CurrentUserDependency,
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
    current_user: CurrentUserDependency,
    item_service: ItemServiceDependency,
) -> Item:
    """Create a new item owned by the authenticated user."""
    return await item_service.create_item(owner_id=current_user.id, data=data)  # type: ignore [arg-type]


@router.patch("/{item_id}", response_model=ItemResponse, summary="Update one of my items")
async def update_my_item(
    item_id: UUID,
    data: ItemUpdate,
    current_user: CurrentUserDependency,
    item_service: ItemServiceDependency,
) -> Item:
    """Partially update a user-owned item and return the updated record."""
    return await item_service.update_item(item_id=item_id, owner_id=current_user.id, data=data)  # type: ignore [arg-type]


@router.delete(
    "/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete one of my items"
)
async def delete_my_item(
    item_id: UUID,
    current_user: CurrentUserDependency,
    item_service: ItemServiceDependency,
) -> None:
    """Delete an item owned by the authenticated user."""
    await item_service.delete_item(item_id=item_id, owner_id=current_user.id)  # type: ignore [arg-type]


# ---------------------------------------------------------------------------
# API7: The user-supplied URL is validated against SSRF attack vectors before
#       the server makes any outbound request.
# API10: The external response is parsed through ExternalItemPayload — a strict
#        Pydantic schema — before any field enters application logic.
# API1: The resulting item is owned by the authenticated user, set server-side.
# ---------------------------------------------------------------------------


@router.post(
    "/import",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import an item from an external URL",
)
async def import_item_from_url(
    data: ItemImportRequest,
    current_user: CurrentUserDependency,
    item_service: ItemServiceDependency,
) -> Item:
    """Fetch item data from a user-supplied URL and create it as a new item."""
    # API7: Block requests to internal/private networks before making the call
    safe_url = validate_ssrf(str(data.url))

    # API10: Fetch and validate the external payload through a strict schema
    external = await fetch_external(
        url=safe_url,
        response_model=ExternalItemPayload,
        service_name=data.url.host if data.url.host else str(data.url),
    )

    # API1: owner_id is always the authenticated user — never from the external payload
    return await item_service.create_item(
        owner_id=current_user.id,  # type: ignore [arg-type]
        data=ItemCreate(
            title=external.title, description=external.description, price=external.price
        ),
    )
