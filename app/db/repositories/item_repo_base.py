"""Abstract item repository interface defining the contract for item data access."""

from app.db.models.item import Item
from app.db.repositories.generic_repo_base import GenericRepositoryBase


class ItemRepositoryBase(GenericRepositoryBase[Item]):
    """Abstract repository interface for Item-specific data access operations."""

    pass
