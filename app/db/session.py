"""Database session management for asynchronous SQLModel operations."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

async_engine = create_async_engine(
    url=settings.database_url,
    echo=settings.database_echo,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Get an asynchronous database session.

    Yields:
        AsyncSession: An asynchronous database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database schema for all registered SQLModel tables."""
    # Import models so SQLModel metadata includes all mapped tables.
    from app.db.models import item, user  # noqa: F401

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
