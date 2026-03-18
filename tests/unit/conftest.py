"""Unit-test fixtures: mock UoW and repository doubles."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.persistence.uow.base import UnitOfWorkBase


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    """AsyncMock for UserRepositoryBase. `add` is sync per the interface."""
    repo = AsyncMock()
    repo.add = MagicMock()
    return repo


@pytest.fixture
def mock_item_repo() -> AsyncMock:
    """AsyncMock for ItemRepositoryBase. `add` is sync per the interface."""
    repo = AsyncMock()
    repo.add = MagicMock()
    return repo


@pytest.fixture
def mock_uow(mock_user_repo: AsyncMock, mock_item_repo: AsyncMock) -> AsyncMock:
    """Fake UnitOfWorkBase with mock repositories."""
    uow = AsyncMock(spec=UnitOfWorkBase)
    uow.users = mock_user_repo
    uow.items = mock_item_repo
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow
