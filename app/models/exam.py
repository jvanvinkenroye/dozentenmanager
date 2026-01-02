"""
Exam model for Dozentenmanager.

This module defines the Exam model representing exams/assessments for courses.
"""

from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from app import db
from app.models.base import TimestampMixin


def validate_max_points(max_points: float) -> bool:
    """
    Validate maximum points for an exam.

    Args:
        max_points: Maximum achievable points

    Returns:
        True if max_points is positive, False otherwise

    Examples:
        >>> validate_max_points(100.0)
        True
        >>> validate_max_points(0.0)
        False
        >>> validate_max_points(-10.0)
        False
    """
    return max_points > 0


def validate_weight(weight: float) -> bool:
    """
    Validate exam weight percentage.

    Args:
        weight: Percentage weight for final grade (0-100)

    Returns:
        True if weight is between 0 and 100 (inclusive), False otherwise

    Examples:
        >>> validate_weight(50.0)
        True
        >>> validate_weight(100.0)
        True
        >>> validate_weight(0.0)
        True
        >>> validate_weight(150.0)
        False
        >>> validate_weight(-10.0)
        False
    """
    return 0 <= weight <= 100


def validate_exam_date(exam_date: date) -> bool:
    """
    Validate exam date.

    Args:
        exam_date: Date of the exam

    Returns:
        True if exam_date is valid (not None), False otherwise

    Examples:
        >>> from datetime import date
        >>> validate_exam_date(date(2024, 6, 15))
        True
        >>> validate_exam_date(None)
        False
    """
    return exam_date is not None


class Exam(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """
    Exam model representing an exam/assessment for a course.

    Attributes:
        id: Unique identifier
        name: Name of the exam (e.g., "Klausur Statistik I")
        course_id: Foreign key to course
        exam_date: Date when the exam takes place
        max_points: Maximum achievable points
        weight: Percentage weight for final grade (0-100, default 100)
        description: Optional description/notes about the exam
        course: Relationship to Course model
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "exam"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False, index=True)
    exam_date = Column(Date, nullable=False, index=True)
    max_points = Column(Float, nullable=False)
    weight = Column(Float, nullable=False, default=100.0)
    description = Column(String(500), nullable=True)

    # Relationship to course
    course = relationship("Course", backref="exams")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_exam_course", "course_id"),
        Index("idx_exam_date", "exam_date"),
    )

    def __repr__(self) -> str:
        """
        String representation of Exam.

        Returns:
            String representation showing id, name, course_id, and exam_date
        """
        return f"<Exam(id={self.id}, name='{self.name}', course_id={self.course_id}, exam_date='{self.exam_date}')>"

    def to_dict(self) -> dict:
        """
        Convert Exam instance to dictionary.

        Returns:
            Dictionary representation of the exam
        """
        return {
            "id": self.id,
            "name": self.name,
            "course_id": self.course_id,
            "exam_date": self.exam_date.isoformat() if self.exam_date else None,
            "max_points": self.max_points,
            "weight": self.weight,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
