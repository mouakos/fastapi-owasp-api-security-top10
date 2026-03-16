"""Shared generic response schemas."""

import math
from typing import TypeVar

from pydantic import BaseModel, computed_field

T = TypeVar("T")


class Page[T](BaseModel):
    """Generic paginated response envelope.

    Attributes:
        items: The list of records for the current page.
        total: Total number of matching records across all pages.
        page: The current 1-based page number.
        size: The number of items per page.
        pages: Total number of pages.
    """

    items: list[T]
    total: int
    page: int
    size: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pages(self) -> int:
        """Total number of pages."""
        return math.ceil(self.total / self.size) if self.size > 0 else 0
