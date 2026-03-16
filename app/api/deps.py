"""FastAPI dependency providers for database and service layer objects."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.persistence.database import AsyncSessionLocal
from app.persistence.models.user import User, UserRole
from app.persistence.uow.base import UnitOfWorkBase
from app.persistence.uow.sqlmodel_uow import SqlModelUnitOfWork
from app.security.jwt import decode_token
from app.services.item_service import ItemService
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token", scheme_name="Bearer", auto_error=False
)


async def get_uow() -> AsyncGenerator[UnitOfWorkBase]:
    """Provide a unit-of-work instance per request.

    The unit of work is instantiated once per request and can be used in
    services as an async context manager to control transaction boundaries.
    """
    sqlmodel_uow = SqlModelUnitOfWork(AsyncSessionLocal)

    async with sqlmodel_uow as uow:
        yield uow


def get_user_service(uow: Annotated[UnitOfWorkBase, Depends(get_uow)]) -> UserService:
    """Provide a user service wired to the current request unit of work."""
    return UserService(uow)


def get_item_service(uow: Annotated[UnitOfWorkBase, Depends(get_uow)]) -> ItemService:
    """Provide an item service wired to the current request unit of work.

    Args:
        uow (UnitOfWorkBase): The unit of work instance for the current request.

    Returns:
        ItemService: An instance of the item service with access to the unit of work.
    """
    return ItemService(uow)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    uow: Annotated[UnitOfWorkBase, Depends(get_uow)],
) -> User:
    """Resolve and return the authenticated user from a bearer token.

    Args:
        token (str): The bearer token extracted from the Authorization header.
        uow (UnitOfWorkBase): The unit of work instance for database access.

    Returns:
        User: The authenticated user associated with the token.

    Raises:
        AuthenticationError: If the token is missing, invalid, or does not correspond to an existing user.
    """
    if not token:
        raise AuthenticationError("Missing authentication token")

    try:
        payload = decode_token(token)
    except Exception as exc:
        raise AuthenticationError("Invalid authentication token") from exc

    if payload is None:
        raise AuthenticationError("Invalid authentication token")

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise AuthenticationError("Invalid authentication token")

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise AuthenticationError("Invalid authentication token") from exc

    async with uow as active_uow:
        user = await active_uow.users.find_by_id(user_id)

    if user is None:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User account is inactive")

    return user


def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure the authenticated user is an admin.

    Args:
        current_user (User): The authenticated and active user.

    Returns:
        User: The same user if they have an admin role.

    Raises:
        AuthorizationError: If the user does not have admin privileges.
    """
    if current_user.role != UserRole.admin:
        raise AuthorizationError("access", "admin resources")
    return current_user


@dataclass
class PaginationParams:
    """Reusable pagination query parameters.

    Attributes:
        page: 1-based page number.
        size: Number of records per page. Capped at 100 (API4).
    """

    page: int = Query(default=1, ge=1, description="Page number (1-based)")
    size: int = Query(default=20, ge=1, le=100, description="Number of items per page")

    @property
    def skip(self) -> int:
        """Compute offset from page number."""
        return (self.page - 1) * self.size


UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
ItemServiceDependency = Annotated[ItemService, Depends(get_item_service)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]
CurrentAdminUserDependency = Annotated[User, Depends(get_current_admin_user)]
PaginationDependency = Annotated[PaginationParams, Depends(PaginationParams)]
