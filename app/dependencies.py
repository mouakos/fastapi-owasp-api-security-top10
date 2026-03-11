"""FastAPI dependency providers for database and service layer objects."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from app.db.session import AsyncSessionLocal
from app.db.uow.base import UnitOfWorkBase
from app.db.uow.sqlmodel_uow import SqlModelUnitOfWork
from app.services.user_services import UserService


async def get_uow() -> AsyncGenerator[UnitOfWorkBase]:
    """Provide a unit-of-work instance per request.

    The unit of work is instantiated once per request and can be used in
    services as an async context manager to control transaction boundaries.
    """
    yield SqlModelUnitOfWork(AsyncSessionLocal)


def get_user_service(uow: Annotated[UnitOfWorkBase, Depends(get_uow)]) -> UserService:
    """Provide a user service wired to the current request unit of work."""
    return UserService(uow)


UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
