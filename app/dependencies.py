"""FastAPI dependency providers for database and service layer objects."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token
from app.db.models.user import User, UserRole
from app.db.session import AsyncSessionLocal
from app.db.uow.base import UnitOfWorkBase
from app.db.uow.sqlmodel_uow import SqlModelUnitOfWork
from app.services.item_service import ItemService
from app.services.user_services import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token", scheme_name="Bearer", auto_error=False
)


async def get_uow() -> AsyncGenerator[UnitOfWorkBase]:
    """Provide a unit-of-work instance per request.

    The unit of work is instantiated once per request and can be used in
    services as an async context manager to control transaction boundaries.
    """
    yield SqlModelUnitOfWork(AsyncSessionLocal)


def get_user_service(uow: Annotated[UnitOfWorkBase, Depends(get_uow)]) -> UserService:
    """Provide a user service wired to the current request unit of work."""
    return UserService(uow)


def get_item_service(uow: Annotated[UnitOfWorkBase, Depends(get_uow)]) -> ItemService:
    """Provide an item service wired to the current request unit of work."""
    return ItemService(uow)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    uow: Annotated[UnitOfWorkBase, Depends(get_uow)],
) -> User:
    """Resolve and return the authenticated user from a bearer token."""
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

    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure the authenticated user is active."""
    if not current_user.is_active:
        raise AuthenticationError("User account is inactive")
    return current_user


def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Ensure the authenticated user is an admin."""
    if current_user.role != UserRole.admin:
        raise AuthorizationError("access", "admin resources")
    return current_user


UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
ItemServiceDependency = Annotated[ItemService, Depends(get_item_service)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]
CurrentActiveUserDependency = Annotated[User, Depends(get_current_active_user)]
CurrentAdminUserDependency = Annotated[User, Depends(get_current_admin_user)]
