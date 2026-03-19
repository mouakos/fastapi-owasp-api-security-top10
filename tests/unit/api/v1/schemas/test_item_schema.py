"""Unit tests for ItemCreate / ItemUpdate Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from app.api.v1.schemas.item import ItemCreate


class TestItemCreate:
    def test_valid_payload_passes(self) -> None:
        item = ItemCreate(title="My Item", price=9.99)
        assert item.title == "My Item"
        assert item.price == 9.99

    def test_optional_description_defaults_to_none(self) -> None:
        item = ItemCreate(title="My Item", price=1.0)
        assert item.description is None

    def test_description_can_be_set(self) -> None:
        item = ItemCreate(title="My Item", description="A desc", price=1.0)
        assert item.description == "A desc"

    def test_empty_title_raises(self) -> None:
        with pytest.raises(ValidationError):
            ItemCreate(title="   ", price=1.0)

    def test_title_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            ItemCreate(title="x" * 201, price=1.0)

    def test_title_is_stripped(self) -> None:
        item = ItemCreate(title="  trimmed  ", price=1.0)
        assert item.title == "trimmed"

    def test_negative_price_raises(self) -> None:
        with pytest.raises(ValidationError):
            ItemCreate(title="Item", price=-1.0)

    def test_zero_price_is_allowed(self) -> None:
        item = ItemCreate(title="Free Item", price=0.0)
        assert item.price == 0.0
