"""
Forms for Dozentenmanager web interface.

This module provides Flask-WTF form classes for data validation.
"""

from app.forms.student import StudentForm
from app.forms.university import UniversityForm
from app.forms.course import CourseForm
from app.forms.exam import ExamForm

__all__ = ["StudentForm", "UniversityForm", "CourseForm", "ExamForm"]
