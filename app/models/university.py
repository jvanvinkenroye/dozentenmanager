"""
University model for Dozentenmanager.

This module defines the University model representing educational institutions.
"""

from sqlalchemy import Column, Integer, String, Index
from app import Base
from app.models.base import TimestampMixin


class University(Base, TimestampMixin):  # type: ignore[misc, valid-type]
    """
    University model representing an educational institution.

    Attributes:
        id: Unique identifier
        name: Full name of the university (required, unique)
        slug: URL-friendly identifier (required, unique)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "university"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)

    # Create index on slug for faster lookups
    __table_args__ = (Index("idx_university_slug", "slug"),)

    def __repr__(self) -> str:
        """
        String representation of University.

        Returns:
            String representation showing id, name, and slug
        """
        return f"<University(id={self.id}, name='{self.name}', slug='{self.slug}')>"

    def to_dict(self) -> dict:
        """
        Convert University instance to dictionary.

        Returns:
            Dictionary representation of the university
        """
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
