"""
Course management CLI tool.

This module provides command-line interface for managing course records,
including adding, updating, listing, and deleting courses.
"""

import argparse
import logging
import sys

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import create_app
from app.services.course_service import CourseService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
        # Initialize service
        service = CourseService()

        try:
            if args.command == "add":
                course = service.add_course(
                    name=args.name,
                    semester=args.semester,
                    university_id=args.university_id,
                    slug=args.slug,
                )
                print("\nCourse added successfully!")
                print(f"ID: {course.id}")
                print(f"Name: {course.name}")
                print(f"Slug: {course.slug}")
                print(f"Semester: {course.semester}")
                print(f"University: {course.university.name}")
                return 0

            if args.command == "list":
                courses = service.list_courses(
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

            if args.command == "show":
                course = service.get_course(args.course_id)
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

            if args.command == "update":
                course = service.update_course(
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
                print("Error: Failed to update course")
                return 1

            if args.command == "delete":
                course = service.get_course(args.course_id)
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

                if service.delete_course(args.course_id):
                    print("Course deleted successfully")
                    return 0
                print("Error: Failed to delete course")
                return 1

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

        except IntegrityError as e:
            logger.error(f"Database constraint error: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}", exc_info=True)
            print("Database error. Please try again.", file=sys.stderr)
            return 1

        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            print("\nOperation cancelled.", file=sys.stderr)
            return 130

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
