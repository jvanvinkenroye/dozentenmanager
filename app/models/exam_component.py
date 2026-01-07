"""
ExamComponent model for Dozentenmanager.

This module defines the ExamComponent model representing individual
weighted components of a multi-part exam (e.g., written part, oral part,
practical project).
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app import db
from app.models.base import TimestampMixin


def validate_component_weight(weight: float) -> bool:
    """
    Validate component weight percentage.

    Args:
        weight: Percentage weight for component (0-100)

    Returns:
        True if weight is between 0 and 100 (exclusive of 0), False otherwise

    Examples:
        >>> validate_component_weight(50.0)
        True
        >>> validate_component_weight(100.0)
        True
        >>> validate_component_weight(0.0)
        False
        >>> validate_component_weight(-10.0)
        False
    """
    return 0 < weight <= 100


def validate_component_max_points(max_points: float) -> bool:
    """
    Validate component maximum points.

    Args:
        max_points: Maximum achievable points for component

    Returns:
        True if max_points is positive, False otherwise

    Examples:
        >>> validate_component_max_points(50.0)
        True
        >>> validate_component_max_points(0.0)
        False
    """
    return max_points > 0


class ExamComponent(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """
    ExamComponent model representing a weighted part of an exam.

    Multi-part exams can have components like:
    - Written exam (60%)
    - Oral presentation (20%)
    - Project work (20%)

    Attributes:
        id: Unique identifier
        exam_id: Foreign key to parent exam
        name: Name of the component (e.g., "Schriftliche Prüfung")
        weight: Percentage weight of this component (0-100)
        max_points: Maximum achievable points for this component
        order: Display order (for sorting components)
        description: Optional description
        exam: Relationship to parent Exam model
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "exam_component"

    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey("exam.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    weight = Column(Float, nullable=False)
    max_points = Column(Float, nullable=False)
    order = Column(Integer, nullable=False, default=0)
    description = Column(String(500), nullable=True)

    # Relationship to exam
    exam = relationship("Exam", backref="components")

    # Constraints
    __table_args__ = (
        CheckConstraint("weight > 0 AND weight <= 100", name="ck_component_weight"),
        CheckConstraint("max_points > 0", name="ck_component_max_points"),
        Index("idx_component_exam", "exam_id"),
        Index("idx_component_order", "exam_id", "order"),
    )

    def __repr__(self) -> str:
        """String representation of ExamComponent."""
        return (
            f"<ExamComponent(id={self.id}, exam_id={self.exam_id}, "
            f"name='{self.name}', weight={self.weight}%)>"
        )

    def to_dict(self) -> dict:
        """
        Convert ExamComponent instance to dictionary.

        Returns:
            Dictionary representation of the component
        """
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "name": self.name,
            "weight": self.weight,
            "max_points": self.max_points,
            "order": self.order,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
