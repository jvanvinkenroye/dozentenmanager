"""
Base model mixins for Dozentenmanager.

This module provides common mixins for database models.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamp columns to models.

    Attributes:
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
    """

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
