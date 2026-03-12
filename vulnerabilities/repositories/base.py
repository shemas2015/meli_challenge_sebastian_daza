"""Base repository interface - Read-only for data access"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Read-only base repository interface

    Provides read-only abstraction layer for data access.
    Write operations (create/update/delete) are handled by Django ORM
    directly in the service/API layer.
    """

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get record by ID

        Args:
            id: Record ID

        Returns:
            Object if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all records with pagination

        Args:
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of objects
        """
        pass

    @abstractmethod
    def exists(self, id: int) -> bool:
        """
        Check if record exists

        Args:
            id: Record ID

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Count total records

        Returns:
            Total number of records
        """
        pass
