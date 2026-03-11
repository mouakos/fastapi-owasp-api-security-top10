"""Abstract user repository interface defining the contract for user data access."""

from abc import abstractmethod

from app.db.models.user import User
from app.db.repositories.generic_repo_base import GenericRepositoryBase


class UserRepositoryBase(GenericRepositoryBase[User]):
    """Abstract repository interface for User-specific data access operations."""

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Fetch a user by email address.

        Args:
            email (str): The email address to search for.

        Returns:
            User | None: The matching user, or None if not found.
        """
        ...

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None:
        """Fetch a user by username.

        Args:
            username (str): The username to search for.

        Returns:
            User | None: The matching user, or None if not found.
        """
        ...
