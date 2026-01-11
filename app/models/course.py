"""
Course model for Dozentenmanager.

This module defines the Course model representing courses offered by universities.
"""

import re

from sqlalchemy import Column, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app import db
from app.models.base import TimestampMixin


def validate_semester(semester: str) -> bool:
    """
    Validate semester format.

    Valid formats:
        - YYYY_SoSe (summer semester, e.g., "2023_SoSe")
        - YYYY_WiSe (winter semester, e.g., "2024_WiSe")

    Args:
        semester: Semester string to validate

    Returns:
        True if semester format is valid, False otherwise

    Examples:
        >>> validate_semester("2023_SoSe")
        True
        >>> validate_semester("2024_WiSe")
        True
        >>> validate_semester("2023")
        False
        >>> validate_semester("2023_SS")
        False
    """
    pattern = r"^\d{4}_(SoSe|WiSe)$"
    return bool(re.match(pattern, semester))


def generate_slug(name: str) -> str:
    """
    Generate a slug from course name.

    Args:
        name: Course name

    Returns:
        Generated slug (lowercase, hyphen-separated)

    Examples:
        >>> generate_slug("Einführung in die Statistik")
        'einfuehrung-in-die-statistik'
        >>> generate_slug("Data Science I")
        'data-science-i'
    """
    # Convert to lowercase
    slug = name.lower()

    # Replace umlauts and special characters
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "é": "e",
        "è": "e",
        "ê": "e",
        "à": "a",
        "á": "a",
        "ì": "i",
        "í": "i",
        "ò": "o",
        "ó": "o",
        "ù": "u",
        "ú": "u",
    }
    for old, new in replacements.items():
        slug = slug.replace(old, new)

    # Remove all characters that are not alphanumeric, space, or hyphen
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)

    # Replace spaces and multiple hyphens with single hyphen
    slug = re.sub(r"[\s-]+", "-", slug)

    # Remove leading/trailing hyphens
    return slug.strip("-")


class Course(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """
    Course model representing a course offered by a university.

    Attributes:
        id: Unique identifier
        name: Full name of the course (required)
        slug: URL-friendly identifier generated from name (required)
        semester: Semester when course is offered (required, format: YYYY_SoSe or YYYY_WiSe)
        university_id: Foreign key to university (required)
        university: Relationship to University model
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "course"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    semester = Column(String(10), nullable=False, index=True)
    university_id = Column(
        Integer, ForeignKey("university.id"), nullable=False, index=True
    )

    # Relationship to university
    university = relationship("University", backref="courses")

    # Unique constraint: one university cannot have duplicate course slugs in the same semester
    __table_args__ = (
        UniqueConstraint(
            "university_id",
            "semester",
            "slug",
            name="uq_course_university_semester_slug",
        ),
        Index("idx_course_university", "university_id"),
        Index("idx_course_semester", "semester"),
    )

    def __repr__(self) -> str:
        """
        String representation of Course.

        Returns:
            String representation showing id, name, semester, and university_id
        """
        return f"<Course(id={self.id}, name='{self.name}', semester='{self.semester}', university_id={self.university_id})>"

    def to_dict(self) -> dict:
        """
        Convert Course instance to dictionary.

        Returns:
            Dictionary representation of the course
        """
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "semester": self.semester,
            "university_id": self.university_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
