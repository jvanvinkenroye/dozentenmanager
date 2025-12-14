"""
ExamComponent model for Dozentenmanager.

This module defines the ExamComponent model representing components/parts of an exam.
"""

from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app import Base
from app.models.base import TimestampMixin


def validate_weight(weight: float) -> bool:
    """
    Validate component weight.

    Weight must be between 0 and 1 (inclusive), representing the percentage
    of the exam grade this component contributes (e.g., 0.4 = 40%).

    Args:
        weight: Weight value to validate

    Returns:
        True if weight is valid, False otherwise

    Examples:
        >>> validate_weight(0.4)
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


def validate_order(order: int) -> bool:
    """
    Validate display order.

    Order must be a non-negative integer.

    Args:
        order: Order value to validate

    Returns:
        True if order is valid, False otherwise

    Examples:
        >>> validate_order(0)
        True
        >>> validate_order(1)
        True
        >>> validate_order(-1)
        False
    """
    return order >= 0


class ExamComponent(Base, TimestampMixin):  # type: ignore[misc, valid-type]
    """
    ExamComponent model representing a component/part of an exam.

    Attributes:
        id: Unique identifier
        name: Name of the component (required, e.g., "Written Part", "Practical Exam")
        description: Optional description of the component
        max_points: Maximum points achievable for this component (required, must be positive)
        weight: Weight in exam grade calculation (required, 0-1, e.g., 0.4 = 40%)
        order: Display order (required, non-negative integer, lower numbers first)
        exam_id: Foreign key to exam (required)
        exam: Relationship to Exam model
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated

    Notes:
        - The sum of weights for all components of an exam should equal 1.0
        - Components are ordered by the 'order' field
    """

    __tablename__ = "exam_component"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    max_points = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    order = Column(Integer, nullable=False, default=0)
    exam_id = Column(Integer, ForeignKey("exam.id"), nullable=False, index=True)

    # Relationship to exam
    exam = relationship("Exam", backref="components")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_exam_component_exam", "exam_id"),
        Index("idx_exam_component_order", "exam_id", "order"),
    )

    def __repr__(self) -> str:
        """
        String representation of ExamComponent.

        Returns:
            String representation showing id, name, and exam_id
        """
        return f"<ExamComponent(id={self.id}, name='{self.name}', exam_id={self.exam_id})>"

    def to_dict(self) -> dict:
        """
        Convert ExamComponent instance to dictionary.

        Returns:
            Dictionary representation of the exam component
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "max_points": self.max_points,
            "weight": self.weight,
            "order": self.order,
            "exam_id": self.exam_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
