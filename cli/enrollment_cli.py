"""
CLI tool for managing enrollments.

This module provides command-line interface for enrolling students in courses.

Usage:
    python cli/enrollment_cli.py add --student-id 12345678 --course-id 1
    python cli/enrollment_cli.py list --course-id 1
    python cli/enrollment_cli.py list --student-id 12345678
    python cli/enrollment_cli.py remove --student-id 12345678 --course-id 1
    python cli/enrollment_cli.py status --student-id 12345678 --course-id 1 --status completed
"""

import argparse
import logging
import sys

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import create_app
from app.models.enrollment import VALID_STATUSES
from app.services.enrollment_service import EnrollmentService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main entry point for enrollment CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Manage student enrollments in courses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enroll a student in a course
  python cli/enrollment_cli.py add --student-id 12345678 --course-id 1

  # List enrollments for a course
  python cli/enrollment_cli.py list --course-id 1

  # List enrollments for a student
  python cli/enrollment_cli.py list --student-id 12345678

  # Remove enrollment
  python cli/enrollment_cli.py remove --student-id 12345678 --course-id 1

  # Update enrollment status
  python cli/enrollment_cli.py status --student-id 12345678 --course-id 1 --status completed
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add enrollment
    add_parser = subparsers.add_parser("add", help="Enroll a student in a course")
    add_parser.add_argument(
        "--student-id",
        required=True,
        help="Student ID (matriculation number)",
    )
    add_parser.add_argument(
        "--course-id",
        type=int,
        required=True,
        help="Course database ID",
    )

    # List enrollments
    list_parser = subparsers.add_parser("list", help="List enrollments")
    list_group = list_parser.add_mutually_exclusive_group(required=True)
    list_group.add_argument(
        "--course-id",
        type=int,
        help="List enrollments for a specific course",
    )
    list_group.add_argument(
        "--student-id",
        help="List enrollments for a specific student",
    )

    # Remove enrollment
    remove_parser = subparsers.add_parser(
        "remove", help="Remove a student's enrollment"
    )
    remove_parser.add_argument(
        "--student-id",
        required=True,
        help="Student ID (matriculation number)",
    )
    remove_parser.add_argument(
        "--course-id",
        type=int,
        required=True,
        help="Course database ID",
    )

    # Update enrollment status
    status_parser = subparsers.add_parser("status", help="Update enrollment status")
    status_parser.add_argument(
        "--student-id",
        required=True,
        help="Student ID (matriculation number)",
    )
    status_parser.add_argument(
        "--course-id",
        type=int,
        required=True,
        help="Course database ID",
    )
    status_parser.add_argument(
        "--status",
        required=True,
        choices=VALID_STATUSES,
        help="New enrollment status",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize Flask app and service
    app = create_app()

    with app.app_context():
        service = EnrollmentService()

        try:
            if args.command == "add":
                enrollment = service.add_enrollment(args.student_id, args.course_id)
                print(
                    f"\nSuccessfully enrolled {enrollment.student.first_name} "
                    f"{enrollment.student.last_name} (ID: {enrollment.student.student_id}) "
                    f"in '{enrollment.course.name}' (Semester: {enrollment.course.semester})"
                )
                return 0

            if args.command == "list":
                enrollments = service.list_enrollments(
                    course_id=args.course_id,
                    student_id_str=args.student_id,
                )

                if not enrollments:
                    print("No enrollments found")
                    return 0

                print(f"\nFound {len(enrollments)} enrollment(s):\n")
                print("=" * 100)
                print(
                    f"{'Student ID':<12} {'Student Name':<25} {'Course':<30} {'Semester':<12} {'Status':<10}"
                )
                print("=" * 100)

                for enrollment in enrollments:
                    student_name = f"{enrollment.student.first_name} {enrollment.student.last_name}"
                    print(
                        f"{enrollment.student.student_id:<12} "
                        f"{student_name:<25} "
                        f"{enrollment.course.name:<30} "
                        f"{enrollment.course.semester:<12} "
                        f"{enrollment.status:<10}"
                    )

                print("=" * 100 + "\n")
                return 0

            if args.command == "remove":
                service.remove_enrollment(args.student_id, args.course_id)
                print(
                    f"\nSuccessfully removed enrollment for student {args.student_id} "
                    f"from course {args.course_id}"
                )
                return 0

            if args.command == "status":
                enrollment = service.update_enrollment_status(
                    args.student_id, args.course_id, args.status
                )
                print(
                    f"\nSuccessfully updated enrollment status to '{args.status}' for "
                    f"{enrollment.student.first_name} {enrollment.student.last_name} "
                    f"in course {enrollment.course.name}"
                )
                return 0

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
