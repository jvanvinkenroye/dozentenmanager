"""
University service for business logic.

This module provides business logic for university management,
separating concerns from CLI and web interfaces.
"""

import logging
import re

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.university import University
from app.services.audit_service import AuditService
from app.services.base_service import BaseService

# Configure logging
logger = logging.getLogger(__name__)


class UniversityService(BaseService):
    """
    Service class for university-related business logic.

    Handles validation, business rules, and database operations
    for university management.
    """

    @staticmethod
    def validate_slug(slug: str) -> bool:
        """
        Validate slug format (lowercase letters, numbers, and hyphens only).

        Args:
            slug: The slug to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
        return bool(re.match(pattern, slug))

    @staticmethod
    def generate_slug(name: str) -> str:
        """
        Generate a slug from university name.

        Args:
            name: University name

        Returns:
            Generated slug (lowercase, hyphen-separated)

        Examples:
            >>> UniversityService.generate_slug("Technische Hochschule Köln")
            'technische-hochschule-koeln'
            >>> UniversityService.generate_slug("TH Köln")
            'th-koeln'
        """
        # Convert to lowercase
        slug = name.lower()

        # Replace umlauts and special characters
        replacements = {
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "ß": "ss",
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
        }
        for char, replacement in replacements.items():
            slug = slug.replace(char, replacement)

        # Remove all non-alphanumeric characters except spaces and hyphens
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)

        # Replace spaces with hyphens
        slug = re.sub(r"\s+", "-", slug)

        # Remove multiple consecutive hyphens
        slug = re.sub(r"-+", "-", slug)

        # Remove leading/trailing hyphens
        return slug.strip("-")

    def add_university(self, name: str, slug: str | None = None) -> University:
        """
        Add a new university to the database.

        Args:
            name: Full name of the university
            slug: URL-friendly identifier (auto-generated if not provided)

        Returns:
            Created University object

        Raises:
            ValueError: If name is empty or slug format is invalid
            IntegrityError: If university with same name or slug already exists
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("University name cannot be empty")

        name = name.strip()

        # Generate or validate slug
        if slug is None:
            slug = self.generate_slug(name)
            logger.info(f"Auto-generated slug: {slug}")
        else:
            slug = slug.strip().lower()
            if not self.validate_slug(slug):
                raise ValueError(
                    f"Invalid slug format: {slug}. "
                    "Slug must contain only lowercase letters, numbers, and hyphens."
                )

        try:
            # Create new university
            university = University(name=name, slug=slug)
            self.add(university)
            self.commit()

            # Log creation
            AuditService.log(
                action="create",
                target_type="University",
                target_id=university.id,
                details={"name": university.name, "slug": university.slug},
            )

            logger.info(f"Successfully created university: {university}")
            return university

        except IntegrityError as e:
            self.rollback()
            if "name" in str(e):
                raise ValueError(f"University with name '{name}' already exists") from e
            if "slug" in str(e):
                raise ValueError(f"University with slug '{slug}' already exists") from e
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while adding university: {e}")
            raise

    def list_universities(self, search: str | None = None) -> list[University]:
        """
        List all universities, optionally filtered by search term.

        Args:
            search: Optional search term to filter by name or slug

        Returns:
            List of University objects
        """
        try:
            query = self.query(University)

            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (University.name.ilike(search_term))
                    | (University.slug.ilike(search_term))
                )

            universities = query.order_by(University.name).all()
            logger.info(f"Found {len(universities)} universities")
            return universities

        except SQLAlchemyError as e:
            logger.error(f"Database error while listing universities: {e}")
            raise

    def get_university(self, university_id: int) -> University | None:
        """
        Get a university by ID.

        Args:
            university_id: University ID

        Returns:
            University object or None if not found
        """
        try:
            university = self.query(University).filter_by(id=university_id).first()

            if university:
                logger.info(f"Found university: {university}")
            else:
                logger.warning(f"University with ID {university_id} not found")

            return university

        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching university: {e}")
            raise

    def update_university(
        self, university_id: int, name: str | None = None, slug: str | None = None
    ) -> University | None:
        """
        Update a university's information.

        Args:
            university_id: University ID
            name: New name (optional)
            slug: New slug (optional)

        Returns:
            Updated University object or None if not found

        Raises:
            ValueError: If validation fails
            IntegrityError: If updated values conflict with existing records
        """
        if name is None and slug is None:
            raise ValueError(
                "At least one field (name or slug) must be provided for update"
            )

        try:
            university = self.query(University).filter_by(id=university_id).first()

            if not university:
                logger.warning(f"University with ID {university_id} not found")
                return None

            # Track changes
            changes = {}

            # Update fields if provided
            if name is not None:
                name = name.strip()
                if not name:
                    raise ValueError("University name cannot be empty")
                if university.name != name:
                    changes["name"] = {"old": university.name, "new": name}
                    university.name = name

            if slug is not None:
                slug = slug.strip().lower()
                if not self.validate_slug(slug):
                    raise ValueError(
                        f"Invalid slug format: {slug}. "
                        "Slug must contain only lowercase letters, numbers, and hyphens."
                    )
                if university.slug != slug:
                    changes["slug"] = {"old": university.slug, "new": slug}
                    university.slug = slug

            if changes:
                self.commit()
                # Log update
                AuditService.log(
                    action="update",
                    target_type="University",
                    target_id=university.id,
                    details=changes,
                )
                logger.info(f"Successfully updated university: {university}")
            return university

        except IntegrityError as e:
            self.rollback()
            if "name" in str(e):
                raise ValueError(f"University with name '{name}' already exists") from e
            if "slug" in str(e):
                raise ValueError(f"University with slug '{slug}' already exists") from e
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while updating university: {e}")
            raise

    def delete_university(self, university_id: int) -> bool:
        """
        Delete a university by ID.

        Args:
            university_id: University ID

        Returns:
            True if deleted, False if not found
        """
        try:
            university = self.query(University).filter_by(id=university_id).first()

            if not university:
                logger.warning(f"University with ID {university_id} not found")
                return False

            university_name = university.name
            university_id_val = university.id

            self.delete(university)
            self.commit()

            # Log deletion
            AuditService.log(
                action="delete",
                target_type="University",
                target_id=university_id_val,
                details={"name": university_name},
            )

            logger.info(f"Successfully deleted university: {university_name}")
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while deleting university: {e}")
            raise
