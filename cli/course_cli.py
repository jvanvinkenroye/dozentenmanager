"""
Course management CLI tool.

This module provides command-line interface for managing course records,
including adding, updating, listing, and deleting courses.
"""

import argparse
import logging
import sys
from typing import Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import app as app_module
from app import create_app
from app.models.course import Course, validate_semester, generate_slug
from app.models.university import University

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def add_course(
    name: str,
    semester: str,
    university_id: int,
    slug: Optional[str] = None,
) -> Optional[Course]:
    """
    Add a new course to the database.

    Args:
        name: Course name
        semester: Semester (format: YYYY_SoSe or YYYY_WiSe)
        university_id: University ID (foreign key)
        slug: Optional custom slug (auto-generated if not provided)

    Returns:
        Created Course object or None if failed

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
        university = (
            app_module.db_session.query(University)  # type: ignore[union-attr]
            .filter_by(id=university_id)
            .first()
        )
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
        app_module.db_session.add(course)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(
            f"Successfully added course: {course.name} ({course.semester}) "
            f"at {university.name}"
        )
        return course

    except IntegrityError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
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
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while adding course: {e}")
        return None


def list_courses(
    university_id: Optional[int] = None, semester: Optional[str] = None
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
        query = app_module.db_session.query(Course)  # type: ignore[union-attr]

        if university_id:
            query = query.filter_by(university_id=university_id)

        if semester:
            query = query.filter_by(semester=semester)

        courses = query.order_by(Course.semester.desc(), Course.name).all()
        return courses

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing courses: {e}")
        return []


def get_course(course_id: int) -> Optional[Course]:
    """
    Get a course by ID.

    Args:
        course_id: Course database ID

    Returns:
        Course object or None if not found
    """
    try:
        course = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .filter_by(id=course_id)
            .first()
        )
        return course

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching course: {e}")
        return None


def update_course(
    course_id: int,
    name: Optional[str] = None,
    semester: Optional[str] = None,
    university_id: Optional[int] = None,
    slug: Optional[str] = None,
) -> Optional[Course]:
    """
    Update an existing course.

    Args:
        course_id: Course database ID
        name: Optional new name
        semester: Optional new semester
        university_id: Optional new university ID
        slug: Optional new slug

    Returns:
        Updated Course object or None if failed

    Raises:
        ValueError: If validation fails
        IntegrityError: If update would violate unique constraint
    """
    try:
        course = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .filter_by(id=course_id)
            .first()
        )

        if not course:
            raise ValueError(f"Course with ID {course_id} not found")

        # Update name and regenerate slug if needed
        if name:
            name = name.strip()
            if not name:
                raise ValueError("Course name cannot be empty")
            if len(name) > 255:
                raise ValueError("Course name cannot exceed 255 characters")
            course.name = name
            # Auto-regenerate slug unless explicitly provided
            if slug is None:
                course.slug = generate_slug(name)

        # Update semester
        if semester:
            semester = semester.strip()
            if not validate_semester(semester):
                raise ValueError(
                    f"Invalid semester format: {semester}. "
                    "Semester must be in format YYYY_SoSe or YYYY_WiSe"
                )
            course.semester = semester

        # Update university
        if university_id:
            university = (
                app_module.db_session.query(University)  # type: ignore[union-attr]
                .filter_by(id=university_id)
                .first()
            )
            if not university:
                raise ValueError(f"University with ID {university_id} not found")
            course.university_id = university_id

        # Update slug if explicitly provided
        if slug:
            slug = slug.strip()
            if len(slug) > 100:
                raise ValueError("Slug cannot exceed 100 characters")
            course.slug = slug

        app_module.db_session.commit()  # type: ignore[union-attr]
        logger.info(f"Successfully updated course: {course.name}")
        return course

    except IntegrityError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        error_msg = str(e)
        if "uq_course_university_semester_slug" in error_msg.lower():
            raise IntegrityError(
                f"Course with slug '{course.slug}' already exists for this university in semester {course.semester}",  # type: ignore[union-attr]
                params=None,
                orig=e.orig,  # type: ignore[arg-type]
            ) from e
        raise

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating course: {e}")
        return None


def delete_course(course_id: int) -> bool:
    """
    Delete a course from the database.

    Args:
        course_id: Course database ID

    Returns:
        True if deleted successfully, False otherwise

    Raises:
        ValueError: If course not found
    """
    try:
        course = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .filter_by(id=course_id)
            .first()
        )

        if not course:
            raise ValueError(f"Course with ID {course_id} not found")

        course_name = course.name
        app_module.db_session.delete(course)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(f"Successfully deleted course: {course_name}")
        return True

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting course: {e}")
        return False


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Course Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add course
    add_parser = subparsers.add_parser("add", help="Add a new course")
    add_parser.add_argument("--name", required=True, help="Course name")
    add_parser.add_argument(
        "--semester",
        required=True,
        help="Semester (format: YYYY_SoSe or YYYY_WiSe, e.g., 2023_SoSe)",
    )
    add_parser.add_argument(
        "--university-id", type=int, required=True, help="University ID"
    )
    add_parser.add_argument(
        "--slug", help="Custom slug (optional, auto-generated if not provided)"
    )

    # List courses
    list_parser = subparsers.add_parser("list", help="List courses")
    list_parser.add_argument(
        "--university-id", type=int, help="Filter by university ID"
    )
    list_parser.add_argument("--semester", help="Filter by semester")

    # Show course details
    show_parser = subparsers.add_parser("show", help="Show course details")
    show_parser.add_argument("course_id", type=int, help="Course ID")

    # Update course
    update_parser = subparsers.add_parser("update", help="Update course")
    update_parser.add_argument("course_id", type=int, help="Course ID")
    update_parser.add_argument("--name", help="New name")
    update_parser.add_argument("--semester", help="New semester")
    update_parser.add_argument("--university-id", type=int, help="New university ID")
    update_parser.add_argument("--slug", help="New slug")

    # Delete course
    delete_parser = subparsers.add_parser("delete", help="Delete course")
    delete_parser.add_argument("course_id", type=int, help="Course ID")
    delete_parser.add_argument("--yes", action="store_true", help="Skip confirmation")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create app and initialize database connection
    app = create_app()
    with app.app_context():
        try:
            if args.command == "add":
                course = add_course(
                    name=args.name,
                    semester=args.semester,
                    university_id=args.university_id,
                    slug=args.slug,
                )
                if course:
                    print("\nCourse added successfully!")
                    print(f"ID: {course.id}")
                    print(f"Name: {course.name}")
                    print(f"Slug: {course.slug}")
                    print(f"Semester: {course.semester}")
                    print(f"University: {course.university.name}")
                    return 0
                else:
                    print("Error: Failed to add course")
                    return 1

            elif args.command == "list":
                courses = list_courses(
                    university_id=args.university_id, semester=args.semester
                )
                if not courses:
                    print("No courses found")
                    return 0

                print(f"\nFound {len(courses)} course(s):\n")
                for course in courses:
                    print(f"ID {course.id}: {course.name}")
                    print(f"  Slug: {course.slug}")
                    print(f"  Semester: {course.semester}")
                    print(f"  University: {course.university.name}")
                    print()
                return 0

            elif args.command == "show":
                course = get_course(args.course_id)
                if not course:
                    print(f"Error: Course with ID {args.course_id} not found")
                    return 1

                print("\nCourse Details:")
                print(f"ID: {course.id}")
                print(f"Name: {course.name}")
                print(f"Slug: {course.slug}")
                print(f"Semester: {course.semester}")
                print(f"University: {course.university.name}")
                print(f"Created: {course.created_at}")
                print(f"Updated: {course.updated_at}")
                return 0

            elif args.command == "update":
                course = update_course(
                    course_id=args.course_id,
                    name=args.name,
                    semester=args.semester,
                    university_id=args.university_id,
                    slug=args.slug,
                )
                if course:
                    print("\nCourse updated successfully!")
                    print(f"ID: {course.id}")
                    print(f"Name: {course.name}")
                    print(f"Slug: {course.slug}")
                    print(f"Semester: {course.semester}")
                    print(f"University: {course.university.name}")
                    return 0
                else:
                    print("Error: Failed to update course")
                    return 1

            elif args.command == "delete":
                course = get_course(args.course_id)
                if not course:
                    print(f"Error: Course with ID {args.course_id} not found")
                    return 1

                if not args.yes:
                    print("\nAre you sure you want to delete this course?")
                    print(f"Name: {course.name}")
                    print(f"Semester: {course.semester}")
                    print(f"University: {course.university.name}")
                    response = input("\nType 'yes' to confirm: ")
                    if response.lower() != "yes":
                        print("Deletion cancelled")
                        return 0

                if delete_course(args.course_id):
                    print("Course deleted successfully")
                    return 0
                else:
                    print("Error: Failed to delete course")
                    return 1

        except ValueError as e:
            print(f"Validation error: {e}")
            return 1
        except IntegrityError as e:
            print(f"Database constraint error: {e}")
            return 1
        except Exception as e:
            logger.exception("Unexpected error")
            print(f"Unexpected error: {e}")
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
