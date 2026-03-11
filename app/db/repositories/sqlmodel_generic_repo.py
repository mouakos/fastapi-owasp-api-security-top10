"""SQLModel async implementation of the GenericRepository interface."""

from typing import Any, TypeVar, override
from uuid import UUID

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.repositories.generic_repo_base import GenericRepositoryBase

ModelT = TypeVar("ModelT", bound=SQLModel)


class SQLModelGenericRepository(GenericRepositoryBase[ModelT]):
    """Async SQLModel implementation of GenericRepository."""

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        """Initialise with the concrete model class and an async session.

        Args:
            model (type[ModelT]): The SQLModel table class to operate on.
            session (AsyncSession): The active async database session.
        """
        self.model = model
        self.session = session

    @override
    def add(self, entity: ModelT) -> None:
        """Stage a new entity for insertion (call flush/commit separately).

        Args:
            entity (ModelT): The entity instance to stage.
        """
        self.session.add(entity)

    @override
    async def find_one(self, **filter: Any) -> ModelT | None:  # noqa: ANN401
        """Find a single entity matching the given filter criteria.

        Args:
            **filter (Any): Column name / value pairs used as WHERE conditions.

        Returns:
            ModelT | None: The first matching record, or None if no match is found.
        """
        result = await self.session.exec(select(self.model).filter_by(**filter))
        return result.first()

    @override
    async def find_by_id(self, id: UUID) -> ModelT | None:  # noqa: A002
        """Return the record with the given primary key, or None.

        Args:
            id (UUID): The primary key of the record to retrieve.

        Returns:
            ModelT | None: The matching record, or None if not found.
        """
        return await self.session.get(self.model, id)

    @override
    async def find_all(self, *, skip: int = 0, limit: int = 20, **filter: Any) -> list[ModelT]:  # noqa: ANN401
        """Return a paginated list of all records.

        Args:
            skip (int, optional): Number of records to skip (offset). Defaults to 0.
            limit (int, optional): Maximum records to return — hard-capped at 100 (API4). Defaults to 20.
            **filter (Any): Column name / value pairs used as WHERE conditions.

        Returns:
            list[ModelT]: A list of all records matching the filter criteria.
        """
        safe_limit = min(limit, 100)  # API4: prevent resource exhaustion
        result = await self.session.exec(
            select(self.model).offset(skip).limit(safe_limit).filter_by(**filter)
        )
        return list(result.all())

    @override
    async def update(self, entity: ModelT, **fields: Any) -> ModelT:  # noqa: ANN401
        """Apply partial field updates, persist, and return the updated record.

        Args:
            entity (ModelT): The existing record to update.
            **fields (Any): Column name / value pairs representing fields to update.

        Returns:
            ModelT: The updated record after applying changes and refreshing from the database.
        """
        for key, value in fields.items():
            setattr(entity, key, value)
        await self.session.merge(entity)
        await self.session.refresh(entity)
        return entity

    @override
    async def delete(self, id: UUID) -> None:  # noqa: A002
        """Delete the record with the given primary key if it exists.

        Args:
            id (UUID): The primary key of the record to delete.
        """
        instance = await self.find_by_id(id)
        if instance is not None:
            await self.session.delete(instance)

    @override
    async def exists(self, id: UUID) -> bool:  # noqa: A002
        """Return True if a record with the given primary key exists.

        Args:
            id (UUID): The primary key to check for existence.

        Returns:
            bool: True if the record exists, False otherwise.
        """
        return await self.session.get(self.model, id) is not None
