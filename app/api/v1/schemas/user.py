"""User request and response schemas.

API3: Separate schemas for CREATE, UPDATE, ADMIN-UPDATE, and RESPONSE ensure
users can never set their own role or expose internal security fields.
"""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from app.db.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for user registration requests.

    Attributes:
        email (EmailStr): A valid, unique email address.
        username (str): A unique username (3-30 alphanumeric chars or underscores).
        password (str): Plain-text password — must meet strength requirements.
    """

    email: EmailStr
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        """Validate that the username matches the allowed pattern.

        Args:
            v (str): The username value to validate.

        Returns:
            str: The validated username.

        Raises:
            ValueError: If the username does not match the required pattern.
        """
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError("Username must be 3-30 alphanumeric characters or underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        """Validate password strength requirements.

        Args:
            v (str): The plain-text password to validate.

        Returns:
            str: The validated password.

        Raises:
            ValueError: If the password fails any strength requirement.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for regular user self-update requests.

    API3: Only the username is patchable by the user themselves.
    Sensitive fields (role, is_active) are intentionally excluded.

    Attributes:
        username (str | None): New username, or None to leave unchanged.
    """

    username: str | None = None

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str | None) -> str | None:
        """Validate the username if provided.

        Args:
            v (str | None): The username value to validate, or None.

        Returns:
            str | None: The validated username, or None if not provided.

        Raises:
            ValueError: If the username does not match the required pattern.
        """
        if v is not None and not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError("Username must be 3-30 alphanumeric characters or underscores")
        return v


class UserAdminUpdate(BaseModel):
    """Schema for admin-only user update requests.

    API5: Role and account status changes are restricted to admin users only.
    This schema must only be accepted on endpoints protected by an admin dependency.

    Attributes:
        role (UserRole | None): New role to assign, or None to leave unchanged.
        is_active (bool | None): Account activation state, or None to leave unchanged.
    """

    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Schema for user data returned in API responses.

    API3: Sensitive fields (hashed_password, failed_login_attempts, locked_until)
    are intentionally excluded and must never be surfaced to clients.

    Attributes:
        id (UUID): The user's unique identifier.
        email (str): The user's email address.
        username (str): The user's username.
        role (UserRole): The user's assigned role.
        is_active (bool): Whether the account is active.
        created_at (datetime): UTC timestamp of account creation.
    """

    id: UUID
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
