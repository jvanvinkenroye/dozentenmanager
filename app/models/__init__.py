"""
Database models for Dozentenmanager.

This module imports all database models to make them available
for the application and Alembic migrations.
"""

# Import models here as they are created
from app.models.course import Course  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.enrollment import Enrollment  # noqa: F401
from app.models.exam import Exam  # noqa: F401
from app.models.exam_component import ExamComponent  # noqa: F401
from app.models.grade import Grade, GradeThreshold, GradingScale  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.submission import Submission  # noqa: F401
from app.models.university import University  # noqa: F401

__all__ = [
    "Course",
    "Document",
    "Enrollment",
    "Exam",
    "ExamComponent",
    "Grade",
    "GradeThreshold",
    "GradingScale",
    "Student",
    "Submission",
    "University",
]
