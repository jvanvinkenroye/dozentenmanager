"""
Base service class for business logic layer.

This module provides a base class that all service classes inherit from,
establishing common patterns and dependencies.
"""

from typing import Any

from app import db


class BaseService:
    """
    Base service class providing common functionality.

    All service classes should inherit from this class to ensure
    consistent patterns and access to shared resources.

    Attributes:
        db: SQLAlchemy database session
    """

    def __init__(self):
        """Initialize the service with database session."""
        self.db = db

    def commit(self) -> None:
        """
        Commit the current database transaction.

        Raises:
            SQLAlchemyError: If commit fails
        """
        self.db.session.commit()

    def rollback(self) -> None:
        """Rollback the current database transaction."""
        self.db.session.rollback()

    def add(self, obj: Any) -> None:
        """
        Add an object to the session.

        Args:
            obj: Object to add to the session
        """
        self.db.session.add(obj)

    def delete(self, obj: Any) -> None:
        """
        Delete an object from the database.

        Args:
            obj: Object to delete
        """
        self.db.session.delete(obj)

    def query(self, model: type) -> Any:
        """
        Create a query for a model.

        Args:
            model: SQLAlchemy model class

        Returns:
            Query object
        """
        return self.db.session.query(model)
