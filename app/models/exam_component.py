"""
ExamComponent model for Dozentenmanager.

This module defines the ExamComponent model representing components/parts of an exam.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app import Base
from app.models.base import TimestampMixin


class ExamComponent(Base, TimestampMixin):  # type: ignore[misc, valid-type]
    """
    ExamComponent model representing a component/part of an exam.

    An exam can be split into multiple components (e.g., "Multiple Choice", "Essay Questions"),
    each with its own max points, weight, and order.

    Attributes:
        id: Unique identifier
        name: Name of the component (required, e.g., "Multiple Choice")
        max_points: Maximum points for this component (required, positive number)
        weight: Weight within the exam (required, 0-1 range)
        order: Display order (required, for sorting components)
        exam_id: Foreign key to exam (required)
        exam: Relationship to Exam model
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "exam_component"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    max_points = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    order = Column(Integer, nullable=False, default=1)
    exam_id = Column(Integer, ForeignKey("exam.id"), nullable=False, index=True)

    # Relationship to exam
    exam = relationship("Exam", backref="components")

    # Unique constraint: exam_id + order must be unique
    __table_args__ = (
        UniqueConstraint("exam_id", "order", name="uq_exam_component_exam_order"),
        Index("idx_exam_component_exam", "exam_id"),
        Index("idx_exam_component_exam_order", "exam_id", "order"),
    )

    def __repr__(self) -> str:
        """
        String representation of ExamComponent.

        Returns:
            String representation showing id, name, exam_id, and order
        """
        return f"<ExamComponent(id={self.id}, name='{self.name}', exam_id={self.exam_id}, order={self.order})>"

    def to_dict(self) -> dict:
        """
        Convert ExamComponent instance to dictionary.

        Returns:
            Dictionary representation of the exam component
        """
        return {
            "id": self.id,
            "name": self.name,
            "max_points": self.max_points,
            "weight": self.weight,
            "order": self.order,
            "exam_id": self.exam_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def validate_component_weights_sum(components: list[ExamComponent]) -> bool:
    """
    Validate that component weights sum to approximately 1.0 for an exam.

    Args:
        components: List of ExamComponent instances for a single exam

    Returns:
        True if weights sum to approximately 1.0, False otherwise

    Examples:
        >>> # This is a conceptual example, actual usage requires database objects
        >>> # If components have weights [0.4, 0.3, 0.3], sum is 1.0
        >>> # validate_component_weights_sum(components) -> True
        True
    """
    if not components:
        return True

    total_weight = sum(comp.weight for comp in components)
    # Allow small floating point differences (0.01)
    return abs(total_weight - 1.0) < 0.01
