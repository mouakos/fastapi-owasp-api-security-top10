"""User service layer for business logic related to users."""

from uuid import UUID

from app.api.v1.schemas.user import UserCreate, UserUpdate
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.db.models.user import User
from app.db.uow.base import UnitOfWorkBase


class UserService:
    """Service layer for user-related business logic."""

    def __init__(self, uow: UnitOfWorkBase) -> None:
        """Initialize the service with a unit of work instance."""
        self._uow = uow

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user with the provided details.

        Args:
            data (UserCreate): The details of the user to create.

        Returns:
            User: The newly created user instance.
        """
        async with self._uow as uow:
            existing_user = await uow.users.find_by_email(data.email)
            if existing_user:
                raise ConflictError("User", "User with this email already exists")

            existing_user = await uow.users.find_by_username(data.username)
            if existing_user:
                raise ConflictError("User", "User with this username already exists")

            new_user = User(
                username=data.username,
                email=data.email,
                hashed_password=hash_password(data.password),
            )

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

    async def get_user_by_id(self, user_id: UUID) -> User:
        """Fetch a user by their ID.

        Args:
            user_id (UUID): The unique identifier of the user to retrieve.

        Returns:
            User: The user with the specified email.

        Raises:
            NotFoundError: If no user with the given ID exists.
        """
        async with self._uow as uow:
            user = await uow.users.find_by_id(user_id)
            if user is None:
                raise NotFoundError("User", user_id)
            return user

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        """Update an existing user's information.

        Args:
            user_id (UUID): The unique identifier of the user to update.
            data (UserUpdate): The fields to update on the user.

        Returns:
            User: The updated user instance.
        """
        async with self._uow as uow:
            user = await uow.users.find_by_id(user_id)
            if user is None:
                raise NotFoundError("User", user_id)

            if data.username is None:
                return user

            existing_user = await uow.users.find_by_username(data.username)
            if existing_user and existing_user.id != user_id:
                raise ConflictError("User", "Username already taken")

            updated_user = await uow.users.update(user, username=data.username)
            await uow.commit()
            return updated_user
