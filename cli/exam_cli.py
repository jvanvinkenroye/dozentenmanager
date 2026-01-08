"""
Exam management CLI tool.

This module provides command-line interface for managing exam records,
including adding, updating, listing, and deleting exams.
"""

import argparse
import logging
import sys
from datetime import datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import create_app
from app.services.exam_service import ExamService

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
        description="Exam Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add exam
    add_parser = subparsers.add_parser("add", help="Add a new exam")
    add_parser.add_argument("--name", required=True, help="Exam name")
    add_parser.add_argument("--course-id", type=int, required=True, help="Course ID")
    add_parser.add_argument(
        "--exam-date",
        required=True,
        help="Exam date (format: YYYY-MM-DD, e.g., 2024-06-15)",
    )
    add_parser.add_argument(
        "--max-points", type=float, required=True, help="Maximum achievable points"
    )
    add_parser.add_argument(
        "--weight",
        type=float,
        default=100.0,
        help="Weight percentage for final grade (0-100, default: 100)",
    )
    add_parser.add_argument("--description", help="Optional description/notes")

    # List exams
    list_parser = subparsers.add_parser("list", help="List exams")
    list_parser.add_argument("--course-id", type=int, help="Filter by course ID")

    # Show exam details
    show_parser = subparsers.add_parser("show", help="Show exam details")
    show_parser.add_argument("exam_id", type=int, help="Exam ID")

    # Update exam
    update_parser = subparsers.add_parser("update", help="Update exam")
    update_parser.add_argument("exam_id", type=int, help="Exam ID")
    update_parser.add_argument("--name", help="New name")
    update_parser.add_argument("--course-id", type=int, help="New course ID")
    update_parser.add_argument("--exam-date", help="New exam date (format: YYYY-MM-DD)")
    update_parser.add_argument("--max-points", type=float, help="New max points")
    update_parser.add_argument("--weight", type=float, help="New weight (0-100)")
    update_parser.add_argument("--description", help="New description")

    # Delete exam
    delete_parser = subparsers.add_parser("delete", help="Delete exam")
    delete_parser.add_argument("exam_id", type=int, help="Exam ID")
    delete_parser.add_argument("--yes", action="store_true", help="Skip confirmation")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create app and initialize database connection
    app = create_app()
    with app.app_context():
        service = ExamService()

        try:
            if args.command == "add":
                # Parse exam date
                try:
                    exam_date = datetime.strptime(args.exam_date, "%Y-%m-%d").date()
                except ValueError as e:
                    print(f"Error: Invalid date format: {e}")
                    print("Use format: YYYY-MM-DD (e.g., 2024-06-15)")
                    return 1

                exam = service.add_exam(
                    name=args.name,
                    course_id=args.course_id,
                    exam_date=exam_date,
                    max_points=args.max_points,
                    weight=args.weight,
                    description=args.description,
                )
                print("\nExam added successfully!")
                print(f"ID: {exam.id}")
                print(f"Name: {exam.name}")
                print(f"Course: {exam.course.name}")
                print(f"Date: {exam.exam_date}")
                print(f"Max Points: {exam.max_points}")
                print(f"Weight: {exam.weight}%")
                if exam.description:
                    print(f"Description: {exam.description}")
                return 0

            if args.command == "list":
                exams = service.list_exams(course_id=args.course_id)
                if not exams:
                    print("No exams found")
                    return 0

                print(f"\nFound {len(exams)} exam(s):\n")
                for exam in exams:
                    print(f"ID {exam.id}: {exam.name}")
                    print(f"  Course: {exam.course.name}")
                    print(f"  Date: {exam.exam_date}")
                    print(f"  Max Points: {exam.max_points}")
                    print(f"  Weight: {exam.weight}%")
                    if exam.description:
                        print(f"  Description: {exam.description}")
                    print()
                return 0

            if args.command == "show":
                exam = service.get_exam(args.exam_id)
                if not exam:
                    print(f"Error: Exam with ID {args.exam_id} not found")
                    return 1

                print("\nExam Details:")
                print(f"ID: {exam.id}")
                print(f"Name: {exam.name}")
                print(f"Course: {exam.course.name}")
                print(f"Date: {exam.exam_date}")
                print(f"Max Points: {exam.max_points}")
                print(f"Weight: {exam.weight}%")
                if exam.description:
                    print(f"Description: {exam.description}")
                print(f"Created: {exam.created_at}")
                print(f"Updated: {exam.updated_at}")
                return 0

            if args.command == "update":
                # Parse exam date if provided
                exam_date = None
                if args.exam_date:
                    try:
                        exam_date = datetime.strptime(args.exam_date, "%Y-%m-%d").date()
                    except ValueError as e:
                        print(f"Error: Invalid date format: {e}")
                        print("Use format: YYYY-MM-DD (e.g., 2024-06-15)")
                        return 1

                exam = service.update_exam(
                    exam_id=args.exam_id,
                    name=args.name,
                    course_id=args.course_id,
                    exam_date=exam_date,
                    max_points=args.max_points,
                    weight=args.weight,
                    description=args.description,
                )
                print("\nExam updated successfully!")
                print(f"ID: {exam.id}")
                print(f"Name: {exam.name}")
                print(f"Course: {exam.course.name}")
                print(f"Date: {exam.exam_date}")
                print(f"Max Points: {exam.max_points}")
                print(f"Weight: {exam.weight}%")
                if exam.description:
                    print(f"Description: {exam.description}")
                return 0

            if args.command == "delete":
                exam = service.get_exam(args.exam_id)
                if not exam:
                    print(f"Error: Exam with ID {args.exam_id} not found")
                    return 1

                if not args.yes:
                    print("\nAre you sure you want to delete this exam?")
                    print(f"Name: {exam.name}")
                    print(f"Course: {exam.course.name}")
                    print(f"Date: {exam.exam_date}")
                    response = input("\nType 'yes' to confirm: ")
                    if response.lower() != "yes":
                        print("Deletion cancelled")
                        return 0

                service.delete_exam(args.exam_id)
                print("Exam deleted successfully")
                return 0

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

        except IntegrityError as e:
            logger.error(f"Database constraint error: {e}")
            print(
                "Database constraint error. Please check your input.", file=sys.stderr
            )
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
