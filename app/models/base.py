"""
Base model mixins for Dozentenmanager.

This module provides common mixins for database models.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamp columns to models.

    Attributes:
        created_at: Timestamp when the record was created (timezone-aware UTC)
        updated_at: Timestamp when the record was last updated (timezone-aware UTC)
    """

    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
