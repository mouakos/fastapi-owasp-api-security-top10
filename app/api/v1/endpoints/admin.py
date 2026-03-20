"""API endpoints for admin operations."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import (
    CurrentAdminUserDependency,
    ItemServiceDependency,
    PaginationDependency,
    UserServiceDependency,
)
from app.api.v1.schemas.common import Page
from app.api.v1.schemas.item import ItemResponse
from app.api.v1.schemas.user import AdminUpdateUserRequest, UserResponse
from app.persistence.models.item import Item
from app.persistence.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# API5: All endpoints are guarded by CurrentAdminUserDependency — only users
#       with the admin role may reach any handler in this router.
# API4: Paginated list endpoints use PaginationDependency to cap page size.
# ---------------------------------------------------------------------------


@router.get("/users", response_model=Page[UserResponse], summary="List all users")
async def list_all_users(
    _: CurrentAdminUserDependency,
    user_service: UserServiceDependency,
    pagination: PaginationDependency,
) -> Page[User]:
    """Return paginated users."""
    users, total = await user_service.list_users(skip=pagination.skip, limit=pagination.size)
    return Page(items=users, total=total, page=pagination.page, size=pagination.size)


@router.patch("/users/{user_id}", response_model=UserResponse, summary="Update a user")
async def update_user(
    _: CurrentAdminUserDependency,
    user_id: UUID,
    data: AdminUpdateUserRequest,
    user_service: UserServiceDependency,
) -> User:
    """Partially update a user and return the updated record."""
    return await user_service.admin_update_user(user_id=user_id, data=data)


@router.get("/items", response_model=Page[ItemResponse], summary="List all items")
async def list_all_items(
    _: CurrentAdminUserDependency,
    item_service: ItemServiceDependency,
    pagination: PaginationDependency,
) -> Page[Item]:
    """Return paginated items."""
    items, total = await item_service.list_items(None, skip=pagination.skip, limit=pagination.size)
    return Page(items=items, total=total, page=pagination.page, size=pagination.size)
