"""
Exam management CLI tool.

This module provides command-line interface for managing exam records,
including adding, updating, listing, and deleting exams.
"""

import argparse
import logging
import sys
from datetime import date, datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import app as app_module
from app import create_app
from app.models.exam import (
    Exam,
    validate_max_points,
    validate_weight,
    validate_exam_date,
)
from app.models.course import Course

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def add_exam(
    name: str,
    course_id: int,
    exam_date: date,
    max_points: float,
    weight: float = 100.0,
    description: Optional[str] = None,
) -> Optional[Exam]:
    """
    Add a new exam to the database.

    Args:
        name: Exam name (e.g., "Klausur Statistik I")
        course_id: Course ID (foreign key)
        exam_date: Date of the exam
        max_points: Maximum achievable points
        weight: Percentage weight for final grade (0-100, default 100)
        description: Optional description/notes

    Returns:
        Created Exam object or None if failed

    Raises:
        ValueError: If validation fails
    """
    # Validate name
    if not name or not name.strip():
        raise ValueError("Exam name cannot be empty")

    name = name.strip()
    if len(name) > 255:
        raise ValueError("Exam name cannot exceed 255 characters")

    # Validate course exists
    try:
        course = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .filter_by(id=course_id)
            .first()
        )
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error while checking course: {e}")
        raise ValueError(f"Error checking course: {e}") from e

    # Validate exam date
    if not validate_exam_date(exam_date):
        raise ValueError("Invalid exam date")

    # Validate max points
    if not validate_max_points(max_points):
        raise ValueError("Maximum points must be greater than 0")

    # Validate weight
    if not validate_weight(weight):
        raise ValueError("Weight must be between 0 and 100")

    # Validate description length
    if description:
        description = description.strip()
        if len(description) > 500:
            raise ValueError("Description cannot exceed 500 characters")

    try:
        # Create new exam
        exam = Exam(
            name=name,
            course_id=course_id,
            exam_date=exam_date,
            max_points=max_points,
            weight=weight,
            description=description,
        )
        app_module.db_session.add(exam)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(
            f"Successfully added exam: {exam.name} for course {course.name} "
            f"on {exam_date}"
        )
        return exam

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while adding exam: {e}")
        return None


def list_exams(course_id: Optional[int] = None) -> list[Exam]:
    """
    List all exams with optional course filter.

    Args:
        course_id: Optional course ID filter

    Returns:
        List of Exam objects matching the filter
    """
    try:
        query = app_module.db_session.query(Exam)  # type: ignore[union-attr]

        if course_id:
            query = query.filter_by(course_id=course_id)

        exams = query.order_by(Exam.exam_date.desc(), Exam.name).all()
        return exams

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing exams: {e}")
        return []


def get_exam(exam_id: int) -> Optional[Exam]:
    """
    Get an exam by ID.

    Args:
        exam_id: Exam database ID

    Returns:
        Exam object or None if not found
    """
    try:
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )
        return exam

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching exam: {e}")
        return None


def update_exam(
    exam_id: int,
    name: Optional[str] = None,
    course_id: Optional[int] = None,
    exam_date: Optional[date] = None,
    max_points: Optional[float] = None,
    weight: Optional[float] = None,
    description: Optional[str] = None,
) -> Optional[Exam]:
    """
    Update an existing exam.

    Args:
        exam_id: Exam database ID
        name: Optional new name
        course_id: Optional new course ID
        exam_date: Optional new exam date
        max_points: Optional new max points
        weight: Optional new weight
        description: Optional new description

    Returns:
        Updated Exam object or None if failed

    Raises:
        ValueError: If validation fails
    """
    try:
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )

        if not exam:
            raise ValueError(f"Exam with ID {exam_id} not found")

        # Update name
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Exam name cannot be empty")
            if len(name) > 255:
                raise ValueError("Exam name cannot exceed 255 characters")
            exam.name = name

        # Update course
        if course_id is not None:
            course = (
                app_module.db_session.query(Course)  # type: ignore[union-attr]
                .filter_by(id=course_id)
                .first()
            )
            if not course:
                raise ValueError(f"Course with ID {course_id} not found")
            exam.course_id = course_id

        # Update exam date
        if exam_date is not None:
            if not validate_exam_date(exam_date):
                raise ValueError("Invalid exam date")
            exam.exam_date = exam_date

        # Update max points
        if max_points is not None:
            if not validate_max_points(max_points):
                raise ValueError("Maximum points must be greater than 0")
            exam.max_points = max_points

        # Update weight
        if weight is not None:
            if not validate_weight(weight):
                raise ValueError("Weight must be between 0 and 100")
            exam.weight = weight

        # Update description
        if description is not None:
            description = description.strip()
            if len(description) > 500:
                raise ValueError("Description cannot exceed 500 characters")
            exam.description = description

        app_module.db_session.commit()  # type: ignore[union-attr]
        logger.info(f"Successfully updated exam: {exam.name}")
        return exam

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating exam: {e}")
        return None


def delete_exam(exam_id: int) -> bool:
    """
    Delete an exam from the database.

    Args:
        exam_id: Exam database ID

    Returns:
        True if deleted successfully, False otherwise

    Raises:
        ValueError: If exam not found
    """
    try:
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )

        if not exam:
            raise ValueError(f"Exam with ID {exam_id} not found")

        exam_name = exam.name
        app_module.db_session.delete(exam)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(f"Successfully deleted exam: {exam_name}")
        return True

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting exam: {e}")
        return False


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
        try:
            if args.command == "add":
                # Parse exam date
                try:
                    exam_date = datetime.strptime(args.exam_date, "%Y-%m-%d").date()
                except ValueError as e:
                    print(f"Error: Invalid date format: {e}")
                    print("Use format: YYYY-MM-DD (e.g., 2024-06-15)")
                    return 1

                exam = add_exam(
                    name=args.name,
                    course_id=args.course_id,
                    exam_date=exam_date,
                    max_points=args.max_points,
                    weight=args.weight,
                    description=args.description,
                )
                if exam:
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
                else:
                    print("Error: Failed to add exam")
                    return 1

            elif args.command == "list":
                exams = list_exams(course_id=args.course_id)
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

            elif args.command == "show":
                exam = get_exam(args.exam_id)
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

            elif args.command == "update":
                # Parse exam date if provided
                exam_date = None
                if args.exam_date:
                    try:
                        exam_date = datetime.strptime(args.exam_date, "%Y-%m-%d").date()
                    except ValueError as e:
                        print(f"Error: Invalid date format: {e}")
                        print("Use format: YYYY-MM-DD (e.g., 2024-06-15)")
                        return 1

                exam = update_exam(
                    exam_id=args.exam_id,
                    name=args.name,
                    course_id=args.course_id,
                    exam_date=exam_date,
                    max_points=args.max_points,
                    weight=args.weight,
                    description=args.description,
                )
                if exam:
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
                else:
                    print("Error: Failed to update exam")
                    return 1

            elif args.command == "delete":
                exam = get_exam(args.exam_id)
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

                if delete_exam(args.exam_id):
                    print("Exam deleted successfully")
                    return 0
                else:
                    print("Error: Failed to delete exam")
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
