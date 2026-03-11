"""API endpoints for admin operations."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.v1.schemas.item import ItemResponse
from app.api.v1.schemas.user import UserAdminUpdate, UserResponse
from app.db.models.item import Item
from app.db.models.user import User
from app.dependencies import (
    CurrentAdminUserDependency,
    ItemServiceDependency,
    UserServiceDependency,
)

router = APIRouter()


@router.get("/users", response_model=list[UserResponse], summary="List all users")
async def list_all_users(
    _: CurrentAdminUserDependency,
    user_service: UserServiceDependency,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[User]:
    """Return paginated users."""
    return await user_service.list_users(skip=skip, limit=limit)


@router.patch("/users/{user_id}", response_model=UserResponse, summary="Update a user")
async def update_user(
    _: CurrentAdminUserDependency,
    user_id: UUID,
    data: UserAdminUpdate,
    user_service: UserServiceDependency,
) -> User:
    """Partially update a user and return the updated record."""
    return await user_service.admin_update_user(user_id=user_id, data=data)


@router.get("/items", response_model=list[ItemResponse], summary="List all items")
async def list_all_items(
    _: CurrentAdminUserDependency,
    item_service: ItemServiceDependency,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Item]:
    """Return paginated items."""
    return await item_service.list_items(None, skip=skip, limit=limit)
