"""User service layer for business logic related to users."""

from datetime import timedelta
from uuid import UUID

from app.api.v1.schemas.auth import Token
from app.api.v1.schemas.user import UserAdminUpdate, UserCreate, UserUpdate
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.persistence.models.user import User
from app.persistence.uow.base import UnitOfWorkBase
from app.security.jwt import create_access_token
from app.security.password import hash_password, verify_password
from app.utils.time import utcnow

LOCKOUT_DURATION_MINUTES = (
    5  # Lockout duration in minutes after reaching maximum failed login attempts
)
MAX_FAILED_ATTEMPTS = 5  # Maximum allowed failed login attempts before lockout


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
        existing_user = await self._uow.users.find_by_email(data.email)
        if existing_user:
            raise ConflictError("User", "User with this email already exists")

        existing_user = await self._uow.users.find_by_username(data.username)
        if existing_user:
            raise ConflictError("User", "User with this username already exists")

        new_user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
        )

        self._uow.users.add(new_user)
        await self._uow.commit()
        return new_user

    async def authenticate_user(self, identifier: str, password: str) -> Token:
        """Authenticate a user by email or username and password.

        Args:
            identifier (str): The email or username of the user.
            password (str): The plaintext password to verify.

        Returns:
            Token: The access token for the authenticated user.

        Raises:
            AuthenticationError: If authentication fails due to invalid credentials.
        """
        user = await self._uow.users.find_by_email(identifier)

        if user is None:
            user = await self._uow.users.find_by_username(identifier)

        # Check for account lockout before verifying password
        if user and user.locked_until and user.locked_until > utcnow():
            raise AuthenticationError(
                "Account is temporarily locked due to multiple failed login attempts. Please try again later."
            )

        if user is None or not verify_password(password, user.hashed_password):
            if user:
                # Increment failed login attempts and apply lockout if necessary
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    user.locked_until = utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                await self._uow.commit()
            raise AuthenticationError("Invalid email/username or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        # Reset failed login attempts on successful authentication
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
            await self._uow.commit()

        access_token = create_access_token({"sub": str(user.id)})
        return Token(access_token=access_token)

    async def get_user_by_id(self, user_id: UUID) -> User:
        """Fetch a user by their ID.

        Args:
            user_id (UUID): The unique identifier of the user to retrieve.

        Returns:
            User: The user with the specified ID.

        Raises:
            NotFoundError: If no user with the given ID exists.
        """
        user = await self._uow.users.find_by_id(user_id)
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
        user = await self._uow.users.find_by_id(user_id)
        if user is None:
            raise NotFoundError("User", user_id)

        if data.username is None:
            return user

        existing_user = await self._uow.users.find_by_username(data.username)
        if existing_user and existing_user.id != user_id:
            raise ConflictError("User", "Username already taken")

        updated_user = await self._uow.users.update(user, username=data.username)
        await self._uow.commit()
        return updated_user

    async def list_users(self, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
        """List users with pagination.

        Args:
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.

        Returns:
            tuple[list[User], int]: A list of users and the total matching count.
        """
        users = await self._uow.users.find_all(skip=skip, limit=limit)
        total = await self._uow.users.count()
        return users, total

    async def admin_update_user(self, user_id: UUID, data: UserAdminUpdate) -> User:
        """Admin-level update of a user's information.

        Args:
            user_id (UUID): The unique identifier of the user to update.
            data (UserAdminUpdate): The fields to update on the user.

        Returns:
            User: The updated user instance.

        Raises:
            NotFoundError: If no user with the given ID exists.
        """
        user = await self.get_user_by_id(user_id)
        updated_user = await self._uow.users.update(user, **data.model_dump(exclude_unset=True))
        await self._uow.commit()
        return updated_user
