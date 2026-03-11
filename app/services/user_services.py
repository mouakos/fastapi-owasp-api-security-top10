"""User service layer for business logic related to users."""

from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.db.models.user import User
from app.db.uow.base import UnitOfWorkBase


class UserService:
    """Service layer for user-related business logic."""

    def __init__(self, uow: UnitOfWorkBase) -> None:
        """Initialize the service with a unit of work instance."""
        self._uow = uow

    async def create_user(self, username: str, email: str, password: str) -> User:
        """Create a new user with the provided details.

        Args:
            username (str): The desired username for the new user.
            email (str): The email address for the new user.
            password (str): The plaintext password for the new user.

        Returns:
            User: The newly created user instance.
        """
        async with self._uow as uow:
            existing_user = await uow.users.find_by_email(email)
            if existing_user:
                raise ConflictError("User")

            existing_user = await uow.users.find_by_username(username)
            if existing_user:
                raise ConflictError("User")

            new_user = User(username=username, email=email, hashed_password=hash_password(password))

            uow.users.add(new_user)
            await uow.commit()
            return new_user

    async def authenticate_user(self, identifier: str, password: str) -> User:
        """Authenticate a user by email or username and password.

        Args:
            identifier (str): The email or username of the user.
            password (str): The plaintext password to verify.

        Returns:
            User: The authenticated user.

        Raises:
            AuthenticationError: If authentication fails due to invalid credentials.
        """
        async with self._uow as uow:
            user = await uow.users.find_by_email(identifier)
            if user is None:
                user = await uow.users.find_by_username(identifier)

            if user is None or not verify_password(password, user.hashed_password):
                raise AuthenticationError("Invalid email/username or password")

            return user

    async def get_user_by_email(self, email: str) -> User:
        """Fetch a user by their email address.

        Args:
            email (str): The email address to search for.

        Returns:
            User: The user with the specified email.

        Raises:
            NotFoundError: If no user with the given email exists.
        """
        async with self._uow as uow:
            user = await uow.users.find_by_email(email)
            if user is None:
                raise NotFoundError("User", email)
            return user
