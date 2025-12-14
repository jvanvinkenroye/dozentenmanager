"""
Exam model for Dozentenmanager.

This module defines the Exam model representing exams for courses.
"""

from sqlalchemy import Column, Integer, String, Text, Date, Float, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from app import Base
from app.models.base import TimestampMixin


def validate_weight(weight: float) -> bool:
    """
    Validate exam weight is between 0 and 1.

    Args:
        weight: Weight value to validate

    Returns:
        True if weight is valid (0 <= weight <= 1), False otherwise

    Examples:
        >>> validate_weight(0.5)
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
    Validate max_points is positive.

    Args:
        max_points: Maximum points to validate

    Returns:
        True if max_points is positive, False otherwise

    Examples:
        >>> validate_max_points(100.0)
        True
        >>> validate_max_points(0.5)
        True
        >>> validate_max_points(0.0)
        False
        >>> validate_max_points(-10.0)
        False
    """
    return max_points > 0.0


class Exam(Base, TimestampMixin):  # type: ignore[misc, valid-type]
    """
    Exam model representing an exam for a course.

    Attributes:
        id: Unique identifier
        name: Name of the exam (required, e.g., "Midterm Exam", "Final Exam")
        description: Detailed description of the exam (optional)
        exam_date: Date when the exam takes place (optional)
        due_date: Due date for exam submission (optional)
        max_points: Maximum points achievable (required, must be positive)
        weight: Weight of this exam in final grade (required, 0.0-1.0)
        course_id: Foreign key to course (required)
        course: Relationship to Course model
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "exam"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    exam_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    max_points = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    course_id = Column(
        Integer, ForeignKey("course.id"), nullable=False, index=True
    )

    # Relationship to course
    course = relationship("Course", backref="exams")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("max_points > 0", name="ck_exam_positive_max_points"),
        CheckConstraint("weight >= 0.0 AND weight <= 1.0", name="ck_exam_weight_range"),
        Index("idx_exam_course", "course_id"),
    )

    def __repr__(self) -> str:
        """
        String representation of Exam.

        Returns:
            String representation showing id, name, max_points, weight, and course_id
        """
        return f"<Exam(id={self.id}, name='{self.name}', max_points={self.max_points}, weight={self.weight}, course_id={self.course_id})>"

    def to_dict(self) -> dict:
        """
        Convert Exam instance to dictionary.

        Returns:
            Dictionary representation of the exam
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "exam_date": self.exam_date.isoformat() if self.exam_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "max_points": self.max_points,
            "weight": self.weight,
            "course_id": self.course_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
