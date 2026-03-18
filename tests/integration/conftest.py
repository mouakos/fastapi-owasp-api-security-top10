"""Integration test fixtures: real UoW backed by in-memory SQLite."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.persistence.uow.sqlmodel_uow import SqlModelUnitOfWork


@pytest.fixture
async def uow(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[SqlModelUnitOfWork]:
    """Function-scoped UoW using the shared in-memory test engine."""
    _uow = SqlModelUnitOfWork(session_factory)
    async with _uow:
        yield _uow
        await _uow.rollback()
