"""Root test configuration: shared async engine and session factory."""

from collections.abc import AsyncGenerator

import pytest
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session", autouse=True)
def silence_loguru() -> None:
    """Remove all loguru sinks so no log output appears during tests."""
    logger.remove()


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    """Session-scoped async engine backed by an in-memory SQLite database."""
    _engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with _engine.begin() as conn:
        from app.persistence.models import Item, User  # noqa: F401

        await conn.run_sync(SQLModel.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest.fixture(scope="session")
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Session-scoped async session factory bound to the test engine."""
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
