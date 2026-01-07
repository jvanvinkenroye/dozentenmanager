"""
Service layer for business logic.

This package contains service classes that handle business logic,
separating concerns from CLI and web interface layers.
"""

from app.services.base_service import BaseService
from app.services.student_service import StudentService
from app.services.university_service import UniversityService

__all__ = [
    "BaseService",
    "StudentService",
    "UniversityService",
]
