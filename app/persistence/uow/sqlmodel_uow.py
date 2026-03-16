"""SQLAlchemy unit-of-work implementation and factory helpers."""

from types import TracebackType

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.persistence.repositories.sqlmodel_item_repo import SQLModelItemRepository
from app.persistence.repositories.sqlmodel_user_repo import SQLModelUserRepository
from app.persistence.uow.base import UnitOfWorkBase


class SqlModelUnitOfWork(UnitOfWorkBase):
    """Manage a SQLAlchemy session and transactional boundaries."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize with a SQLAlchemy session factory."""
        self.session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "SqlModelUnitOfWork":
        """Open a new session and initialize repositories."""
        self._session = self.session_factory()
        self.users = SQLModelUserRepository(self._session)
        self.items = SQLModelItemRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Roll back on error and always close the current session."""
        if self._session is None:
            return

        try:
            if exc_type:
                await self.rollback()
        finally:
            await self._session.close()

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._session is None:
            raise RuntimeError("Session is not initialized.")
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        if self._session is None:
            raise RuntimeError("Session is not initialized.")
        await self._session.rollback()
