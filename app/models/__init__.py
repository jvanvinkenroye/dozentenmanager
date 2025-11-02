"""
Database models for Dozentenmanager.

This module imports all database models to make them available
for the application and Alembic migrations.
"""

# Import models here as they are created
from app.models.course import Course  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.university import University  # noqa: F401
# from app.models.enrollment import Enrollment
# from app.models.exam import Exam
# from app.models.exam_component import ExamComponent
# from app.models.submission import Submission
# from app.models.document import Document
# from app.models.audit_log import AuditLog

__all__ = [
    "Course",
    "Student",
    "University",
    # List other model names here as they are created
]
