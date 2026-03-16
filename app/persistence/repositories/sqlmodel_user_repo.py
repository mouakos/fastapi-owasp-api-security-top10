"""SQLModel async implementation of the UserRepository interface."""

from typing import override

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.persistence.models.user import User
from app.persistence.repositories.sqlmodel_generic_repo import SQLModelGenericRepository
from app.persistence.repositories.user_repo_base import UserRepositoryBase


class SQLModelUserRepository(SQLModelGenericRepository[User], UserRepositoryBase):
    """Concrete async SQLModel implementation of UserRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialise with an async database session.

        Args:
            session (AsyncSession): The active async database session.
        """
        super().__init__(User, session)

    @override
    async def find_by_email(self, email: str) -> User | None:
        """Fetch a user by email address.

        Args:
            email (str): The email address to search for.

        Returns:
            User | None: The matching user, or None if not found.
        """
        result = await self.session.exec(select(User).where(User.email == email))
        return result.first()

    @override
    async def find_by_username(self, username: str) -> User | None:
        """Fetch a user by username.

        Args:
            username (str): The username to search for.

        Returns:
            User | None: The matching user, or None if not found.
        """
        result = await self.session.exec(select(User).where(User.username == username))
        return result.first()
