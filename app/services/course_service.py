"""
Course service for business logic.

This module provides business logic for course management,
separating concerns from CLI and web interfaces.
"""

import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.course import Course, generate_slug, validate_semester
from app.models.university import University
from app.services.base_service import BaseService

# Configure logging
logger = logging.getLogger(__name__)


class CourseService(BaseService):
    """
    Service class for course-related business logic.

    Handles validation, business rules, and database operations
    for course management.
    """

    def add_course(
        self,
        name: str,
        semester: str,
        university_id: int,
        slug: str | None = None,
    ) -> Course:
        """
        Add a new course to the database.

        Args:
            name: Course name
            semester: Semester (format: YYYY_SoSe or YYYY_WiSe)
            university_id: University ID (foreign key)
            slug: Optional custom slug (auto-generated if not provided)

        Returns:
            Created Course object

        Raises:
            ValueError: If validation fails
            IntegrityError: If course with same university_id+semester+slug already exists
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Course name cannot be empty")

        name = name.strip()
        if len(name) > 255:
            raise ValueError("Course name cannot exceed 255 characters")

        # Validate semester
        semester = semester.strip()
        if not validate_semester(semester):
            raise ValueError(
                f"Invalid semester format: {semester}. "
                "Semester must be in format YYYY_SoSe or YYYY_WiSe (e.g., 2023_SoSe, 2024_WiSe)"
            )

        # Validate university exists
        try:
            university = self.query(University).filter_by(id=university_id).first()
            if not university:
                raise ValueError(f"University with ID {university_id} not found")
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking university: {e}")
            raise ValueError(f"Error checking university: {e}") from e

        # Generate or validate slug
        if slug:
            slug = slug.strip()
            if len(slug) > 100:
                raise ValueError("Slug cannot exceed 100 characters")
            # Basic slug validation
            if not slug.replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    "Slug can only contain lowercase letters, numbers, and hyphens"
                )
        else:
            slug = generate_slug(name)

        try:
            # Create new course
            course = Course(
                name=name,
                semester=semester,
                university_id=university_id,
                slug=slug,
            )
            self.add(course)
            self.commit()

            logger.info(
                f"Successfully added course: {course.name} ({course.semester}) "
                f"at {university.name}"
            )
            return course

        except IntegrityError as e:
            self.rollback()
            error_msg = str(e)
            if "uq_course_university_semester_slug" in error_msg.lower():
                raise IntegrityError(
                    f"Course with slug '{slug}' already exists for {university.name} "
                    f"in semester {semester}",
                    params=None,
                    orig=e.orig,  # type: ignore[arg-type]
                ) from e
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while adding course: {e}")
            raise

    def list_courses(
        self, university_id: int | None = None, semester: str | None = None
    ) -> list[Course]:
        """
        List all courses with optional filters.

        Args:
            university_id: Optional university ID filter
            semester: Optional semester filter

        Returns:
            List of Course objects matching the filters
        """
        try:
            query = self.query(Course)

            if university_id:
                query = query.filter_by(university_id=university_id)

            if semester:
                query = query.filter_by(semester=semester)

            return query.order_by(Course.semester.desc(), Course.name).all()

        except SQLAlchemyError as e:
            logger.error(f"Database error while listing courses: {e}")
            raise

    def get_course(self, course_id: int) -> Course | None:
        """
        Get a course by ID.

        Args:
            course_id: Course database ID

        Returns:
            Course object or None if not found
        """
        try:
            course = self.query(Course).filter_by(id=course_id).first()

            if course:
                logger.info(f"Found course: {course}")
            else:
                logger.warning(f"Course with ID {course_id} not found")

            return course

        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching course: {e}")
            raise

    def update_course(
        self,
        course_id: int,
        name: str | None = None,
        semester: str | None = None,
        university_id: int | None = None,
        slug: str | None = None,
    ) -> Course | None:
        """
        Update a course's information.

        Args:
            course_id: Course database ID
            name: New name (optional)
            semester: New semester (optional)
            university_id: New university ID (optional)
            slug: New slug (optional)

        Returns:
            Updated Course object or None if not found

        Raises:
            ValueError: If validation fails
            IntegrityError: If updated values conflict with existing records
        """
        if all(v is None for v in [name, semester, university_id, slug]):
            raise ValueError("At least one field must be provided for update")

        try:
            course = self.query(Course).filter_by(id=course_id).first()

            if not course:
                raise ValueError(f"Course with ID {course_id} not found")

            # Update fields if provided
            if name is not None:
                name = name.strip()
                if not name:
                    raise ValueError("Course name cannot be empty")
                if len(name) > 255:
                    raise ValueError("Course name cannot exceed 255 characters")
                course.name = name
                # Auto-regenerate slug unless explicitly provided
                if slug is None:
                    course.slug = generate_slug(name)

            if semester is not None:
                semester = semester.strip()
                if not validate_semester(semester):
                    raise ValueError(
                        f"Invalid semester format: {semester}. "
                        "Semester must be in format YYYY_SoSe or YYYY_WiSe"
                    )
                course.semester = semester

            if university_id is not None:
                university = self.query(University).filter_by(id=university_id).first()
                if not university:
                    raise ValueError(f"University with ID {university_id} not found")
                course.university_id = university_id

            if slug is not None:
                slug = slug.strip()
                if len(slug) > 100:
                    raise ValueError("Slug cannot exceed 100 characters")
                if not slug.replace("-", "").replace("_", "").isalnum():
                    raise ValueError(
                        "Slug can only contain lowercase letters, numbers, and hyphens"
                    )
                course.slug = slug

            self.commit()
            logger.info(f"Successfully updated course: {course}")
            return course

        except IntegrityError as e:
            self.rollback()
            error_msg = str(e)
            if "uq_course_university_semester_slug" in error_msg.lower():
                raise IntegrityError(
                    "Course with this slug already exists for this university and semester",
                    params=None,
                    orig=e.orig,  # type: ignore[arg-type]
                ) from e
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while updating course: {e}")
            raise

    def delete_course(self, course_id: int) -> bool:
        """
        Delete a course by ID.

        Args:
            course_id: Course database ID

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If course not found
        """
        try:
            course = self.query(Course).filter_by(id=course_id).first()

            if not course:
                raise ValueError(f"Course with ID {course_id} not found")

            self.delete(course)
            self.commit()
            logger.info(f"Successfully deleted course: {course}")
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while deleting course: {e}")
            raise
