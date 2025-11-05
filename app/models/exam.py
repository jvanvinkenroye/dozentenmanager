"""
Exam model for Dozentenmanager.

This module defines the Exam model representing exams for courses.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app import Base
from app.models.base import TimestampMixin


def validate_weight(weight: float) -> bool:
    """
    Validate exam weight.

    Weight must be between 0 and 1 (inclusive), representing the percentage
    of the final grade this exam contributes (e.g., 0.3 = 30%).

    Args:
        weight: Weight value to validate

    Returns:
        True if weight is valid, False otherwise

    Examples:
        >>> validate_weight(0.3)
        True
        >>> validate_weight(1.0)
        True
        >>> validate_weight(0.0)
        True
        >>> validate_weight(1.5)
        False
        >>> validate_weight(-0.1)
        False
    """
    return 0.0 <= weight <= 1.0


def validate_max_points(max_points: float) -> bool:
    """
    Validate maximum points.

    Maximum points must be positive.

    Args:
        max_points: Maximum points value to validate

    Returns:
        True if max_points is valid, False otherwise

    Examples:
        >>> validate_max_points(100.0)
        True
        >>> validate_max_points(50.5)
        True
        >>> validate_max_points(0.0)
        False
        >>> validate_max_points(-10.0)
        False
    """
    return max_points > 0


def validate_due_date(due_date: Optional[datetime]) -> bool:
    """
    Validate due date.

    Due date can be None (no due date) or any datetime value.
    Optionally, you could add logic to ensure it's not in the past.

    Args:
        due_date: Due date to validate

    Returns:
        True if due_date is valid

    Examples:
        >>> validate_due_date(None)
        True
        >>> from datetime import datetime
        >>> validate_due_date(datetime(2024, 12, 31))
        True
    """
    # For now, accept any due date including None
    # You could add: return due_date is None or due_date > datetime.now()
    return True


class Exam(Base, TimestampMixin):  # type: ignore[misc, valid-type]
    """
    Exam model representing an exam or assessment for a course.

    Attributes:
        id: Unique identifier
        name: Name of the exam (required, e.g., "Midterm Exam", "Final Project")
        exam_type: Type of exam (required, e.g., "midterm", "final", "quiz", "homework", "project")
        due_date: Due date for submissions (optional)
        max_points: Maximum points achievable (required, must be positive)
        weight: Weight in final grade calculation (required, 0-1, e.g., 0.3 = 30%)
        course_id: Foreign key to course (required)
        course: Relationship to Course model
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "exam"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    exam_type = Column(String(50), nullable=False, index=True)
    due_date = Column(DateTime, nullable=True)
    max_points = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False, index=True)

    # Relationship to course
    course = relationship("Course", backref="exams")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_exam_course", "course_id"),
        Index("idx_exam_type", "exam_type"),
        Index("idx_exam_due_date", "due_date"),
    )

    def __repr__(self) -> str:
        """
        String representation of Exam.

        Returns:
            String representation showing id, name, exam_type, and course_id
        """
        return f"<Exam(id={self.id}, name='{self.name}', exam_type='{self.exam_type}', course_id={self.course_id})>"

    def to_dict(self) -> dict:
        """
        Convert Exam instance to dictionary.

        Returns:
            Dictionary representation of the exam
        """
        return {
            "id": self.id,
            "name": self.name,
            "exam_type": self.exam_type,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "max_points": self.max_points,
            "weight": self.weight,
            "course_id": self.course_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
