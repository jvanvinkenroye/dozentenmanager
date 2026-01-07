"""
Student management CLI tool.

This module provides command-line interface for managing student records,
including adding, updating, listing, and deleting students.
"""

import argparse
import logging
import sys

from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.services.student_service import StudentService

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
        description="Student management CLI tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new student")
    add_parser.add_argument("--first-name", required=True, help="First name")
    add_parser.add_argument("--last-name", required=True, help="Last name")
    add_parser.add_argument("--student-id", required=True, help="Student ID (8 digits)")
    add_parser.add_argument("--email", required=True, help="Email address")
    add_parser.add_argument("--program", required=True, help="Study program/major")

    # List command
    list_parser = subparsers.add_parser("list", help="List all students")
    list_parser.add_argument("--search", help="Search by name, student ID, or email")
    list_parser.add_argument("--program", help="Filter by program")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show student details")
    show_parser.add_argument("id", type=int, help="Database ID")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update a student")
    update_parser.add_argument("id", type=int, help="Database ID")
    update_parser.add_argument("--first-name", help="New first name")
    update_parser.add_argument("--last-name", help="New last name")
    update_parser.add_argument("--student-id", help="New student ID")
    update_parser.add_argument("--email", help="New email")
    update_parser.add_argument("--program", help="New program")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a student")
    delete_parser.add_argument("id", type=int, help="Database ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create Flask app context for database access
    app = create_app()

    with app.app_context():
        # Initialize service
        service = StudentService()

        try:
            if args.command == "add":
                student = service.add_student(
                    args.first_name,
                    args.last_name,
                    args.student_id,
                    args.email,
                    args.program,
                )
                print(
                    f"Created student: ID={student.id}, "
                    f"Name={student.first_name} {student.last_name}, "
                    f"Student ID={student.student_id}, "
                    f"Email={student.email}"
                )
                return 0

            if args.command == "list":
                students = service.list_students(args.search, args.program)
                if students:
                    print(f"\nFound {len(students)} students:\n")
                    print(
                        f"{'DB ID':<7} {'Student ID':<12} {'Name':<35} {'Email':<35} {'Program':<30}"
                    )
                    print("-" * 125)
                    for student in students:
                        name = f"{student.first_name} {student.last_name}"
                        print(
                            f"{student.id:<7} {student.student_id:<12} {name:<35} {student.email:<35} {student.program:<30}"
                        )
                else:
                    print("No students found")
                return 0

            if args.command == "show":
                student = service.get_student(args.id)
                if student:
                    print("\nStudent Details:")
                    print(f"  Database ID: {student.id}")
                    print(f"  Student ID: {student.student_id}")
                    print(f"  Name: {student.first_name} {student.last_name}")
                    print(f"  Email: {student.email}")
                    print(f"  Program: {student.program}")
                    print(f"  Created: {student.created_at}")
                    print(f"  Updated: {student.updated_at}")
                else:
                    print(f"Student with ID {args.id} not found")
                    return 1
                return 0

            if args.command == "update":
                student = service.update_student(
                    args.id,
                    args.first_name,
                    args.last_name,
                    args.student_id,
                    args.email,
                    args.program,
                )
                if student:
                    print(
                        f"Updated student: ID={student.id}, "
                        f"Name={student.first_name} {student.last_name}, "
                        f"Student ID={student.student_id}, "
                        f"Email={student.email}"
                    )
                    return 0
                print(f"Student with ID {args.id} not found")
                return 1

            if args.command == "delete":
                if service.delete_student(args.id):
                    print(f"Student with ID {args.id} deleted successfully")
                    return 0
                print(f"Student with ID {args.id} not found")
                return 1

        except ValueError as e:
            logger.error(f"Validation error: {e}")
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
