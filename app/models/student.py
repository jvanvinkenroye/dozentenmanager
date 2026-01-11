"""
Student model for Dozentenmanager.

This module defines the Student model representing students in the system.
"""

import re
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Index, Integer, String

from app import db
from app.models.base import TimestampMixin


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_email("student@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_student_id(student_id: str) -> bool:
    """
    Validate student ID format (8 digits).

    Args:
        student_id: Student ID to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_student_id("12345678")
        True
        >>> validate_student_id("123")
        False
        >>> validate_student_id("abcd1234")
        False
    """
    return bool(re.match(r"^\d{8}$", student_id))


class Student(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """
    Student model representing a student in the system.

    Attributes:
        id: Unique identifier
        first_name: Student's first name (required)
        last_name: Student's last name (required)
        student_id: Student ID number (required, unique, 8 digits)
        email: Email address (required, unique)
        program: Study program/major (required)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "student"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, index=True)
    student_id = Column(String(8), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    program = Column(String(200), nullable=False)
    deleted_at = Column(DateTime, nullable=True, index=True)

    # Create composite index for common queries
    __table_args__ = (
        Index("idx_student_name", "last_name", "first_name"),
        Index("idx_student_student_id", "student_id"),
        Index("idx_student_email", "email"),
    )

    def __repr__(self) -> str:
        """
        String representation of Student.

        Returns:
            String representation showing id, name, and student_id
        """
        return f"<Student(id={self.id}, name='{self.first_name} {self.last_name}', student_id='{self.student_id}')>"

    def to_dict(self) -> dict:
        """
        Convert Student instance to dictionary.

        Returns:
            Dictionary representation of the student
        """
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "student_id": self.student_id,
            "email": self.email,
            "program": self.program,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def soft_delete(self) -> None:
        """Mark student as deleted without removing the record."""
        self.deleted_at = datetime.now(UTC)  # type: ignore[assignment]
