"""
Submission model for Dozentenmanager.

This module defines the Submission model representing student submissions
for enrollments (documents, assignments, exam answers, etc.).
"""

from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app import db
from app.models.base import TimestampMixin

# Valid submission types
VALID_SUBMISSION_TYPES = ["document", "assignment", "exam_answer", "email_attachment"]

# Valid submission statuses
VALID_SUBMISSION_STATUSES = ["submitted", "reviewed", "graded", "returned"]


def validate_submission_type(submission_type: str) -> bool:
    """
    Validate submission type.

    Args:
        submission_type: Type value to validate

    Returns:
        True if type is valid, False otherwise

    Examples:
        >>> validate_submission_type("document")
        True
        >>> validate_submission_type("invalid")
        False
    """
    return submission_type in VALID_SUBMISSION_TYPES


def validate_submission_status(status: str) -> bool:
    """
    Validate submission status.

    Args:
        status: Status value to validate

    Returns:
        True if status is valid, False otherwise

    Examples:
        >>> validate_submission_status("submitted")
        True
        >>> validate_submission_status("invalid")
        False
    """
    return status in VALID_SUBMISSION_STATUSES


class Submission(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """
    Submission model representing a student submission.

    Attributes:
        id: Unique submission identifier
        enrollment_id: Foreign key to Enrollment
        exam_id: Optional foreign key to Exam (if submission is for an exam)
        submission_type: Type of submission (document, assignment, exam_answer, email_attachment)
        submission_date: Date and time when submission was made
        status: Submission status (submitted, reviewed, graded, returned)
        notes: Optional notes about the submission
        enrollment: Relationship to Enrollment model
        exam: Relationship to Exam model (optional)
        documents: Relationship to Document model (one-to-many)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "submission"

    id = Column(Integer, primary_key=True)
    enrollment_id = Column(
        Integer, ForeignKey("enrollment.id"), nullable=False, index=True
    )
    exam_id = Column(Integer, ForeignKey("exam.id"), nullable=True, index=True)
    submission_type = Column(String(50), nullable=False, default="document")
    submission_date = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    status = Column(String(20), nullable=False, default="submitted", index=True)
    notes = Column(Text, nullable=True)

    # Relationships
    enrollment = relationship("Enrollment", backref="submissions")
    exam = relationship("Exam", backref="submissions")
    documents = relationship(
        "Document",
        backref="submission",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "submission_type IN ('document', 'assignment', 'exam_answer', 'email_attachment')",
            name="ck_submission_type",
        ),
        CheckConstraint(
            "status IN ('submitted', 'reviewed', 'graded', 'returned')",
            name="ck_submission_status",
        ),
        Index("idx_submission_enrollment", "enrollment_id"),
        Index("idx_submission_exam", "exam_id"),
        Index("idx_submission_status", "status"),
    )

    def __repr__(self) -> str:
        """String representation of Submission."""
        return (
            f"<Submission(id={self.id}, enrollment_id={self.enrollment_id}, "
            f"type={self.submission_type}, status={self.status})>"
        )

    def to_dict(self) -> dict:
        """
        Convert Submission instance to dictionary.

        Returns:
            Dictionary representation of the submission
        """
        return {
            "id": self.id,
            "enrollment_id": self.enrollment_id,
            "exam_id": self.exam_id,
            "submission_type": self.submission_type,
            "submission_date": (
                self.submission_date.isoformat() if self.submission_date else None
            ),
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
