"""User model definition for the FastAPI app."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

from app.db.models.item import Item
from app.utils.time import utcnow


class UserRole(enum.StrEnum):
    """User roles for access control."""

    user = "user"
    admin = "admin"


class User(SQLModel, table=True):
    """User model representing application users."""

    __tablename__ = "users"

    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    role: UserRole = Field(
        default=UserRole.user,
        sa_column=Column(
            SAEnum(UserRole, name="userrole", values_callable=lambda x: [e.value for e in x]),
            nullable=False,
            default=UserRole.user,
            index=True,
        ),
    )
    is_active: bool = Field(default=True)

    # API2: Track failed logins for account lockout
    failed_login_attempts: int = Field(default=0)
    # Stores naive UTC datetime; NULL = not locked
    locked_until: datetime | None = Field(default=None)

    created_at: datetime = Field(default_factory=utcnow)

    items: list[Item] = Relationship(
        back_populates="owner", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
