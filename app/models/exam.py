"""
Exam model for Dozentenmanager.

This module defines the Exam model representing exams for courses.
"""

from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from app import Base
from app.models.base import TimestampMixin


def validate_weight(weight: float) -> bool:
    """
    Validate that weight is in valid range (0-1).

    Args:
        weight: Weight value to validate

    Returns:
        True if weight is valid, False otherwise

    Examples:
        >>> validate_weight(0.6)
        True
        >>> validate_weight(1.0)
        True
        >>> validate_weight(-0.1)
        False
        >>> validate_weight(1.5)
        False
    """
    return 0.0 <= weight <= 1.0


def validate_max_points(max_points: float) -> bool:
    """
    Validate that max_points is positive.

    Args:
        max_points: Maximum points value to validate

    Returns:
        True if max_points is valid, False otherwise

    Examples:
        >>> validate_max_points(100.0)
        True
        >>> validate_max_points(0.1)
        True
        >>> validate_max_points(0.0)
        False
        >>> validate_max_points(-10.0)
        False
    """
    return max_points > 0.0


def validate_due_date(due_date: date, allow_past: bool = False) -> bool:
    """
    Validate that due date is not in the past (when creating).

    Args:
        due_date: Due date to validate
        allow_past: If True, allow dates in the past (for updates)

    Returns:
        True if due date is valid, False otherwise

    Examples:
        >>> from datetime import date, timedelta
        >>> future_date = date.today() + timedelta(days=30)
        >>> validate_due_date(future_date)
        True
        >>> validate_due_date(future_date, allow_past=True)
        True
        >>> past_date = date.today() - timedelta(days=30)
        >>> validate_due_date(past_date)
        False
        >>> validate_due_date(past_date, allow_past=True)
        True
    """
    if allow_past:
        return True
    return due_date >= date.today()


class Exam(Base, TimestampMixin):  # type: ignore[misc, valid-type]
    """
    Exam model representing an exam for a course.

    Attributes:
        id: Unique identifier
        name: Name of the exam (required, e.g., "Final Exam")
        max_points: Maximum points possible (required, positive number)
        weight: Weight in final grade (required, 0-1 range)
        due_date: Date when exam is due (optional)
        course_id: Foreign key to course (required)
        course: Relationship to Course model
        components: Relationship to ExamComponent models
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "exam"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    max_points = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    due_date = Column(Date, nullable=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False, index=True)

    # Relationship to course
    course = relationship("Course", backref="exams")

    # Relationship to exam components (will be defined in exam_component.py)
    # components = relationship("ExamComponent", backref="exam", order_by="ExamComponent.order")

    __table_args__ = (Index("idx_exam_course", "course_id"),)

    def __repr__(self) -> str:
        """
        String representation of Exam.

        Returns:
            String representation showing id, name, and course_id
        """
        return f"<Exam(id={self.id}, name='{self.name}', course_id={self.course_id}, max_points={self.max_points})>"

    def to_dict(self) -> dict:
        """
        Convert Exam instance to dictionary.

        Returns:
            Dictionary representation of the exam
        """
        return {
            "id": self.id,
            "name": self.name,
            "max_points": self.max_points,
            "weight": self.weight,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "course_id": self.course_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
