"""Abstract unit-of-work contract used to coordinate database transactions."""

from abc import ABC, abstractmethod
from types import TracebackType

from app.db.repositories.item_repo_base import ItemRepositoryBase
from app.db.repositories.user_repo_base import UserRepositoryBase


class UnitOfWorkBase(ABC):
    """Coordinate transactional work across one or more repositories.

    Implementations are expected to be used as context managers so resource
    acquisition and cleanup are handled consistently.
    """

    # Repositories are accessed as attributes
    users: UserRepositoryBase
    items: ItemRepositoryBase

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWorkBase":
        """Enter the unit-of-work context and begin a transaction."""
        return self

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the context and roll back if an exception occurred."""
        pass

    @abstractmethod
    async def commit(self) -> None:
        """Commit all changes made within this unit of work."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback all changes made within this unit of work."""
        pass
