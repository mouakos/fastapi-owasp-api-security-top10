"""Item model definition for the FastAPI app."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from app.utils.time import utcnow

if TYPE_CHECKING:
    from app.db.models.user import User


class Item(SQLModel, table=True):
    """Item model representing products or services in the application."""

    __tablename__ = "items"

    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    title: str
    description: str | None = Field(default=None)
    price: float
    is_active: bool = Field(default=True)
    owner_id: UUID = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=utcnow)

    owner: Optional["User"] = Relationship(back_populates="items")
