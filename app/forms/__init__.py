"""
Forms for Dozentenmanager web interface.

This module provides Flask-WTF form classes for data validation.
"""

from app.forms.course import CourseForm
from app.forms.document import (
    BulkDocumentUploadForm,
    DocumentSearchForm,
    DocumentUploadForm,
    SubmissionStatusForm,
)
from app.forms.email import EmailImportForm
from app.forms.exam import ExamForm
from app.forms.grade import (
    BulkGradeForm,
    ExamComponentForm,
    GradeFilterForm,
    GradeForm,
    GradeSearchForm,
)
from app.forms.student import StudentForm, StudentImportForm
from app.forms.university import UniversityForm

__all__ = [
    "BulkDocumentUploadForm",
    "BulkGradeForm",
    "CourseForm",
    "DocumentSearchForm",
    "DocumentUploadForm",
    "EmailImportForm",
    "ExamComponentForm",
    "ExamForm",
    "GradeFilterForm",
    "GradeForm",
    "GradeSearchForm",
    "StudentForm",
    "StudentImportForm",
    "SubmissionStatusForm",
    "UniversityForm",
]
