"""Item request and response schemas.

API3: Separate schemas for CREATE, UPDATE, and RESPONSE ensure owner_id and
internal fields can never be set directly by the client.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl, field_validator


class ItemImportRequest(BaseModel):
    """Schema for importing an item from an external URL.

    API7: The url field is validated against SSRF attack vectors before the
          server makes any outbound request.

    Attributes:
        url (HttpUrl): The public HTTPS endpoint that returns item JSON.
    """

    url: HttpUrl


class ExternalItemPayload(BaseModel):
    """Schema used to validate the JSON returned by an external item source.

    API10: Raw data from the upstream service is parsed through this strict
           schema before any field is used in application logic.  Fields not
           declared here are silently ignored; missing or wrongly-typed fields
           raise a validation error that is surfaced as ExternalServiceError.

    Attributes:
        title (str): The item title.
        description (str | None): An optional description.
        price (float): The item price — must be non-negative.
    """

    title: str
    description: str | None = None
    price: float


class ItemCreate(BaseModel):
    """Schema for item creation requests.

    Attributes:
        title (str): The item title (1-200 non-blank characters).
        description (str | None): An optional description. Defaults to None.
        price (float): The item price — must be non-negative, rounded to 2 decimal places.
    """

    title: str
    description: str | None = None
    price: float

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate that the title is non-blank and within the length limit.

        Args:
            v (str): The raw title value.

        Returns:
            str: The stripped, validated title.

        Raises:
            ValueError: If the title is blank or exceeds 200 characters.
        """
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        if len(v) > 200:
            raise ValueError("Title cannot exceed 200 characters")
        return v

    @field_validator("price")
    @classmethod
    def price_non_negative(cls, v: float) -> float:
        """Validate that the price is non-negative and normalize to 2 decimal places.

        Args:
            v (float): The raw price value.

        Returns:
            float: The validated price rounded to 2 decimal places.

        Raises:
            ValueError: If the price is negative.
        """
        if v < 0:
            raise ValueError("Price must be non-negative")
        return round(v, 2)


class ItemUpdate(BaseModel):
    """Schema for partial item update requests.

    All fields are optional — only provided fields will be updated.

    Attributes:
        title (str | None): New title, or None to leave unchanged.
        description (str | None): New description, or None to leave unchanged.
        price (float | None): New price, or None to leave unchanged.
    """

    title: str | None = None
    description: str | None = None
    price: float | None = None


class ItemResponse(BaseModel):
    """Schema for item data returned in API responses.

    API3: owner_id is included so clients can verify ownership, but internal
    fields (e.g. soft-delete flags) are intentionally excluded.

    Attributes:
        id (UUID): The item's unique identifier.
        title (str): The item title.
        description (str | None): The item description, if any.
        price (float): The item price.
        is_active (bool): Whether the item is currently active.
        owner_id (UUID): The UUID of the user who owns this item.
        created_at (datetime): UTC timestamp of when the item was created.
    """

    id: UUID
    title: str
    description: str | None = None
    price: float
    is_active: bool
    owner_id: UUID
    created_at: datetime
