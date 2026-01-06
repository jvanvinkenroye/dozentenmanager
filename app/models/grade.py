"""
Grade model for Dozentenmanager.

This module defines the Grade model for tracking student grades on exams
and exam components, as well as the GradingScale model for defining
grade thresholds.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app import db
from app.models.base import TimestampMixin


# German grading scale (default)
GERMAN_GRADES = {
    1.0: (95, 100, "sehr gut"),
    1.3: (90, 94, "sehr gut"),
    1.7: (85, 89, "gut"),
    2.0: (80, 84, "gut"),
    2.3: (75, 79, "gut"),
    2.7: (70, 74, "befriedigend"),
    3.0: (65, 69, "befriedigend"),
    3.3: (60, 64, "befriedigend"),
    3.7: (55, 59, "ausreichend"),
    4.0: (50, 54, "ausreichend"),
    5.0: (0, 49, "nicht ausreichend"),
}


def calculate_percentage(points: float, max_points: float) -> float:
    """
    Calculate percentage from points.

    Args:
        points: Achieved points
        max_points: Maximum possible points

    Returns:
        Percentage (0-100)

    Examples:
        >>> calculate_percentage(80, 100)
        80.0
        >>> calculate_percentage(45, 90)
        50.0
    """
    if max_points <= 0:
        return 0.0
    return round((points / max_points) * 100, 2)


def percentage_to_german_grade(percentage: float) -> tuple[float, str]:
    """
    Convert percentage to German grade.

    Args:
        percentage: Achievement percentage (0-100)

    Returns:
        Tuple of (grade_value, grade_description)

    Examples:
        >>> percentage_to_german_grade(95)
        (1.0, 'sehr gut')
        >>> percentage_to_german_grade(75)
        (2.3, 'gut')
        >>> percentage_to_german_grade(45)
        (5.0, 'nicht ausreichend')
    """
    for grade_value, (min_pct, max_pct, description) in GERMAN_GRADES.items():
        if min_pct <= percentage <= max_pct:
            return grade_value, description
    return 5.0, "nicht ausreichend"


def validate_points(points: float, max_points: float) -> bool:
    """
    Validate that points are within valid range.

    Args:
        points: Achieved points
        max_points: Maximum possible points

    Returns:
        True if points are valid (0 to max_points), False otherwise

    Examples:
        >>> validate_points(80, 100)
        True
        >>> validate_points(-5, 100)
        False
        >>> validate_points(110, 100)
        False
    """
    return 0 <= points <= max_points


class GradingScale(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """
    GradingScale model for defining custom grading thresholds.

    Allows universities or courses to define their own grading scales.

    Attributes:
        id: Unique identifier
        name: Name of the grading scale (e.g., "Deutsche Notenskala")
        university_id: Optional foreign key to University (for university-specific scales)
        is_default: Whether this is the default scale for the university
        description: Optional description
        thresholds: Relationship to GradeThreshold entries
    """

    __tablename__ = "grading_scale"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    university_id = Column(
        Integer, ForeignKey("university.id"), nullable=True, index=True
    )
    is_default = Column(Boolean, nullable=False, default=False)
    description = Column(String(500), nullable=True)

    # Relationships
    university = relationship("University", backref="grading_scales")
    thresholds = relationship(
        "GradeThreshold",
        backref="scale",
        cascade="all, delete-orphan",
        order_by="GradeThreshold.min_percentage.desc()",
    )

    # Constraints
    __table_args__ = (
        Index("idx_grading_scale_university", "university_id"),
    )

    def __repr__(self) -> str:
        """String representation of GradingScale."""
        return f"<GradingScale(id={self.id}, name='{self.name}')>"

    def get_grade(self, percentage: float) -> Optional["GradeThreshold"]:
        """
        Get the grade threshold for a given percentage.

        Args:
            percentage: Achievement percentage (0-100)

        Returns:
            GradeThreshold matching the percentage, or None
        """
        for threshold in self.thresholds:
            if percentage >= threshold.min_percentage:
                return threshold
        return None

    def to_dict(self) -> dict:
        """Convert GradingScale instance to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "university_id": self.university_id,
            "is_default": self.is_default,
            "description": self.description,
            "thresholds": [t.to_dict() for t in self.thresholds],
        }


class GradeThreshold(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """
    GradeThreshold model for defining grade boundaries.

    Each threshold defines the minimum percentage needed for a grade.

    Attributes:
        id: Unique identifier
        scale_id: Foreign key to GradingScale
        grade_value: Numeric grade value (e.g., 1.0, 1.3, 2.0)
        grade_label: Display label (e.g., "sehr gut", "A+")
        min_percentage: Minimum percentage to achieve this grade
        description: Optional description
    """

    __tablename__ = "grade_threshold"

    id = Column(Integer, primary_key=True)
    scale_id = Column(
        Integer, ForeignKey("grading_scale.id"), nullable=False, index=True
    )
    grade_value = Column(Float, nullable=False)
    grade_label = Column(String(50), nullable=False)
    min_percentage = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "min_percentage >= 0 AND min_percentage <= 100",
            name="ck_threshold_percentage",
        ),
        UniqueConstraint(
            "scale_id", "grade_value", name="uq_threshold_scale_grade"
        ),
        Index("idx_threshold_scale", "scale_id"),
        Index("idx_threshold_percentage", "min_percentage"),
    )

    def __repr__(self) -> str:
        """String representation of GradeThreshold."""
        return (
            f"<GradeThreshold(grade={self.grade_value}, "
            f"label='{self.grade_label}', min={self.min_percentage}%)>"
        )

    def to_dict(self) -> dict:
        """Convert GradeThreshold instance to dictionary."""
        return {
            "id": self.id,
            "scale_id": self.scale_id,
            "grade_value": self.grade_value,
            "grade_label": self.grade_label,
            "min_percentage": self.min_percentage,
            "description": self.description,
        }


class Grade(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """
    Grade model for tracking student grades on exams/components.

    Attributes:
        id: Unique identifier
        enrollment_id: Foreign key to Enrollment
        exam_id: Foreign key to Exam
        component_id: Optional foreign key to ExamComponent (for multi-part exams)
        points: Points achieved by student
        percentage: Calculated percentage (auto-computed)
        grade_value: Numeric grade value (e.g., 1.0, 2.3)
        grade_label: Grade label (e.g., "sehr gut", "gut")
        graded_at: Timestamp when grade was assigned
        graded_by: Username/ID of person who graded
        is_final: Whether this is the final grade (vs. preliminary)
        notes: Optional grading notes
        enrollment: Relationship to Enrollment
        exam: Relationship to Exam
        component: Relationship to ExamComponent (optional)
    """

    __tablename__ = "grade"

    id = Column(Integer, primary_key=True)
    enrollment_id = Column(
        Integer, ForeignKey("enrollment.id"), nullable=False, index=True
    )
    exam_id = Column(Integer, ForeignKey("exam.id"), nullable=False, index=True)
    component_id = Column(
        Integer, ForeignKey("exam_component.id"), nullable=True, index=True
    )
    points = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    grade_value = Column(Float, nullable=True)
    grade_label = Column(String(50), nullable=True)
    graded_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    graded_by = Column(String(100), nullable=True)
    is_final = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)

    # Relationships
    enrollment = relationship("Enrollment", backref="grades")
    exam = relationship("Exam", backref="grades")
    component = relationship("ExamComponent", backref="grades")

    # Constraints
    __table_args__ = (
        CheckConstraint("points >= 0", name="ck_grade_points"),
        CheckConstraint(
            "percentage >= 0 AND percentage <= 100", name="ck_grade_percentage"
        ),
        UniqueConstraint(
            "enrollment_id",
            "exam_id",
            "component_id",
            name="uq_grade_enrollment_exam_component",
        ),
        Index("idx_grade_enrollment", "enrollment_id"),
        Index("idx_grade_exam", "exam_id"),
        Index("idx_grade_component", "component_id"),
        Index("idx_grade_final", "is_final"),
    )

    def __repr__(self) -> str:
        """String representation of Grade."""
        return (
            f"<Grade(id={self.id}, enrollment_id={self.enrollment_id}, "
            f"exam_id={self.exam_id}, points={self.points}, "
            f"grade={self.grade_value})>"
        )

    def to_dict(self) -> dict:
        """Convert Grade instance to dictionary."""
        return {
            "id": self.id,
            "enrollment_id": self.enrollment_id,
            "exam_id": self.exam_id,
            "component_id": self.component_id,
            "points": self.points,
            "percentage": self.percentage,
            "grade_value": self.grade_value,
            "grade_label": self.grade_label,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "graded_by": self.graded_by,
            "is_final": self.is_final,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_with_auto_grade(
        cls,
        enrollment_id: int,
        exam_id: int,
        points: float,
        max_points: float,
        component_id: Optional[int] = None,
        graded_by: Optional[str] = None,
        is_final: bool = False,
        notes: Optional[str] = None,
        grading_scale: Optional[GradingScale] = None,
    ) -> "Grade":
        """
        Create a Grade with automatic percentage and grade calculation.

        Args:
            enrollment_id: Enrollment ID
            exam_id: Exam ID
            points: Points achieved
            max_points: Maximum possible points
            component_id: Optional component ID for multi-part exams
            graded_by: Who assigned the grade
            is_final: Whether grade is final
            notes: Optional notes
            grading_scale: Optional custom grading scale (uses German default if None)

        Returns:
            New Grade instance (not yet committed to database)

        Raises:
            ValueError: If points are invalid
        """
        if not validate_points(points, max_points):
            raise ValueError(
                f"Points must be between 0 and {max_points}, got {points}"
            )

        percentage = calculate_percentage(points, max_points)

        # Calculate grade
        if grading_scale:
            threshold = grading_scale.get_grade(percentage)
            if threshold:
                grade_value = threshold.grade_value
                grade_label = threshold.grade_label
            else:
                grade_value = 5.0
                grade_label = "nicht ausreichend"
        else:
            grade_value, grade_label = percentage_to_german_grade(percentage)

        return cls(
            enrollment_id=enrollment_id,
            exam_id=exam_id,
            component_id=component_id,
            points=points,
            percentage=percentage,
            grade_value=grade_value,
            grade_label=grade_label,
            graded_by=graded_by,
            is_final=is_final,
            notes=notes,
        )
