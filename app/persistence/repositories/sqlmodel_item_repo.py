"""SQLModel async implementation of the ItemRepository interface."""

from sqlmodel.ext.asyncio.session import AsyncSession

from app.persistence.models.item import Item
from app.persistence.repositories.item_repo_base import ItemRepositoryBase
from app.persistence.repositories.sqlmodel_generic_repo import SQLModelGenericRepository


class SQLModelItemRepository(SQLModelGenericRepository[Item], ItemRepositoryBase):
    """Concrete async SQLModel implementation of ItemRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialise with an async database session.

        Args:
            session (AsyncSession): The active async database session.
        """
        super().__init__(Item, session)
