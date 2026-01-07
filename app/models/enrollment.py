"""
Enrollment model.

This module defines the Enrollment model representing the many-to-many
relationship between students and courses.
"""

from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app import db

# Valid enrollment status values
VALID_STATUSES = ["active", "completed", "dropped"]


def validate_status(status: str) -> bool:
    """
    Validate enrollment status.

    Args:
        status: Status value to validate

    Returns:
        True if status is valid, False otherwise
    """
    return status in VALID_STATUSES


class Enrollment(db.Model):  # type: ignore[name-defined]
    """
    Enrollment model representing student enrollment in courses.

    Attributes:
        id: Unique enrollment identifier
        student_id: Foreign key to Student
        course_id: Foreign key to Course
        enrollment_date: Date when student enrolled (defaults to today)
        unenrollment_date: Date when student unenrolled (nullable)
        status: Enrollment status (active, completed, dropped)
        student: Relationship to Student model
        course: Relationship to Course model
    """

    __tablename__ = "enrollment"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False, index=True)
    enrollment_date = Column(Date, nullable=False, default=date.today)
    unenrollment_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="active", index=True)

    # Relationships
    student = relationship("Student", backref="enrollments")
    course = relationship("Course", backref="enrollments")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", name="uq_enrollment_student_course"
        ),
        CheckConstraint(
            "status IN ('active', 'completed', 'dropped')",
            name="ck_enrollment_status",
        ),
    )

    def __repr__(self) -> str:
        """String representation of Enrollment."""
        return f"<Enrollment(id={self.id}, student_id={self.student_id}, course_id={self.course_id}, status={self.status})>"
