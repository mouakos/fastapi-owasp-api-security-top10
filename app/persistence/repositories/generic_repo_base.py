"""Generic repository interface defining the contract for data access operations on domain entities."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar
from uuid import UUID

# Generic type variable for domain entities
T = TypeVar("T")


class GenericRepositoryBase[T](ABC):
    """Abstract base class for repositories handling domain entities of type T."""

    @abstractmethod
    def add(self, entity: T) -> None:
        """Add a new entity to the repository.

        Args:
            entity (T): The entity to add.
        """
        ...

    @abstractmethod
    async def find_one(self, **filter: Any) -> T | None:  # noqa: ANN401
        """Find a single entity matching the given filter criteria.

        Args:
            **filter (Any): Arbitrary keyword arguments representing filter criteria.

        Returns:
            T | None: The found entity or None if no match is found.
        """
        ...

    @abstractmethod
    async def find_by_id(self, id: UUID) -> T | None:  # noqa: A002
        """Find an entity by its unique identifier.

        Args:
            id (UUID): The unique identifier of the entity to retrieve.

        Returns:
            T | None: The found entity or None if no match is found.
        """
        ...

    @abstractmethod
    async def find_all(self, *, skip: int = 0, limit: int = 20, **filter: Any) -> list[T]:  # noqa: ANN401
        """Find all entities matching the given filter criteria.

        Args:
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.
            **filter (Any): Arbitrary keyword arguments representing filter criteria.

        Returns:
            list[T]: A list of all entities matching the filter criteria.
        """
        ...

    @abstractmethod
    async def update(self, entity: T, **fields: Any) -> T:  # noqa: ANN401
        """Update an existing entity with the provided fields.

        Args:
            entity (T): The entity to update.
            **fields: Fields to update on the entity.

        Returns:
            T: The updated entity.
        """
        ...

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        """Remove an entity by its identifier.

        Args:
            id (UUID): The unique identifier of the entity to delete.
        """
        ...

    @abstractmethod
    async def count(self, **filter: Any) -> int:  # noqa: ANN401
        """Return the total number of entities matching the given filter.

        Args:
            **filter (Any): Arbitrary keyword arguments representing filter criteria.

        Returns:
            int: The total number of matching entities.
        """
        ...

    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """Check if an entity with the given identifier exists.

        Args:
            id (UUID): The unique identifier to check for existence.

        Returns:
            bool: True if the entity exists, False otherwise.
        """
        ...
