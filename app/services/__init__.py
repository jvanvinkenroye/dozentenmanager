"""
Service layer for business logic.

This package contains service classes that handle business logic,
separating concerns from CLI and web interface layers.
"""

from app.services.base_service import BaseService
from app.services.university_service import UniversityService

__all__ = [
    "BaseService",
    "UniversityService",
]
