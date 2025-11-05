"""
Exam management CLI tool.

This module provides command-line interface for managing exam records,
including adding, updating, listing, and deleting exams.
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import app as app_module
from app import create_app
from app.models.course import Course
from app.models.exam import Exam, validate_weight, validate_max_points

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def add_exam(
    name: str,
    exam_type: str,
    max_points: float,
    weight: float,
    course_id: int,
    due_date: Optional[datetime] = None,
) -> Optional[Exam]:
    """
    Add a new exam to the database.

    Args:
        name: Exam name (e.g., "Midterm Exam", "Final Project")
        exam_type: Type of exam (e.g., "midterm", "final", "quiz", "homework", "project")
        max_points: Maximum points achievable (must be positive)
        weight: Weight in final grade (0-1, e.g., 0.3 = 30%)
        course_id: Course ID (foreign key)
        due_date: Optional due date for submissions

    Returns:
        Created Exam object or None if failed

    Raises:
        ValueError: If validation fails
        IntegrityError: If database constraint is violated
    """
    # Validate name
    if not name or not name.strip():
        raise ValueError("Exam name cannot be empty")

    name = name.strip()
    if len(name) > 255:
        raise ValueError("Exam name cannot exceed 255 characters")

    # Validate exam_type
    if not exam_type or not exam_type.strip():
        raise ValueError("Exam type cannot be empty")

    exam_type = exam_type.strip().lower()
    if len(exam_type) > 50:
        raise ValueError("Exam type cannot exceed 50 characters")

    # Validate max_points
    if not validate_max_points(max_points):
        raise ValueError(
            f"Invalid max_points: {max_points}. "
            "Maximum points must be a positive number."
        )

    # Validate weight
    if not validate_weight(weight):
        raise ValueError(
            f"Invalid weight: {weight}. "
            "Weight must be between 0 and 1 (e.g., 0.3 for 30%)."
        )

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

    try:
        # Create new exam
        exam = Exam(
            name=name,
            exam_type=exam_type,
            max_points=max_points,
            weight=weight,
            course_id=course_id,
            due_date=due_date,
        )
        app_module.db_session.add(exam)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(
            f"Successfully added exam: {exam.name} ({exam.exam_type}) "
            f"for course {course.name}"
        )
        return exam

    except IntegrityError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database integrity error while adding exam: {e}")
        raise

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while adding exam: {e}")
        return None


def list_exams(
    course_id: Optional[int] = None,
    exam_type: Optional[str] = None,
) -> list[Exam]:
    """
    List all exams with optional filters.

    Args:
        course_id: Optional course ID filter
        exam_type: Optional exam type filter

    Returns:
        List of Exam objects matching the filters
    """
    try:
        query = app_module.db_session.query(Exam)  # type: ignore[union-attr]

        if course_id:
            query = query.filter_by(course_id=course_id)

        if exam_type:
            query = query.filter_by(exam_type=exam_type.lower())

        exams = query.order_by(Exam.due_date.asc(), Exam.name).all()
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
    exam_type: Optional[str] = None,
    max_points: Optional[float] = None,
    weight: Optional[float] = None,
    course_id: Optional[int] = None,
    due_date: Optional[datetime] = None,
    clear_due_date: bool = False,
) -> Optional[Exam]:
    """
    Update an existing exam.

    Args:
        exam_id: Exam database ID
        name: Optional new name
        exam_type: Optional new exam type
        max_points: Optional new max_points
        weight: Optional new weight
        course_id: Optional new course ID
        due_date: Optional new due date
        clear_due_date: If True, clear the due_date (set to None)

    Returns:
        Updated Exam object or None if failed

    Raises:
        ValueError: If validation fails
        IntegrityError: If update would violate database constraint
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
        if name:
            name = name.strip()
            if not name:
                raise ValueError("Exam name cannot be empty")
            if len(name) > 255:
                raise ValueError("Exam name cannot exceed 255 characters")
            exam.name = name

        # Update exam_type
        if exam_type:
            exam_type = exam_type.strip().lower()
            if not exam_type:
                raise ValueError("Exam type cannot be empty")
            if len(exam_type) > 50:
                raise ValueError("Exam type cannot exceed 50 characters")
            exam.exam_type = exam_type

        # Update max_points
        if max_points is not None:
            if not validate_max_points(max_points):
                raise ValueError(
                    f"Invalid max_points: {max_points}. "
                    "Maximum points must be a positive number."
                )
            exam.max_points = max_points

        # Update weight
        if weight is not None:
            if not validate_weight(weight):
                raise ValueError(
                    f"Invalid weight: {weight}. "
                    "Weight must be between 0 and 1 (e.g., 0.3 for 30%)."
                )
            exam.weight = weight

        # Update course
        if course_id:
            course = (
                app_module.db_session.query(Course)  # type: ignore[union-attr]
                .filter_by(id=course_id)
                .first()
            )
            if not course:
                raise ValueError(f"Course with ID {course_id} not found")
            exam.course_id = course_id

        # Update or clear due_date
        if clear_due_date:
            exam.due_date = None
        elif due_date is not None:
            exam.due_date = due_date

        app_module.db_session.commit()  # type: ignore[union-attr]
        logger.info(f"Successfully updated exam: {exam.name}")
        return exam

    except IntegrityError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database integrity error while updating exam: {e}")
        raise

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
    add_parser.add_argument(
        "--exam-type",
        required=True,
        help="Exam type (e.g., midterm, final, quiz, homework, project)",
    )
    add_parser.add_argument(
        "--max-points",
        type=float,
        required=True,
        help="Maximum points (must be positive)",
    )
    add_parser.add_argument(
        "--weight",
        type=float,
        required=True,
        help="Weight in final grade (0-1, e.g., 0.3 for 30%%)",
    )
    add_parser.add_argument("--course-id", type=int, required=True, help="Course ID")
    add_parser.add_argument(
        "--due-date",
        help="Due date (format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)",
    )

    # List exams
    list_parser = subparsers.add_parser("list", help="List exams")
    list_parser.add_argument("--course-id", type=int, help="Filter by course ID")
    list_parser.add_argument("--exam-type", help="Filter by exam type")

    # Show exam details
    show_parser = subparsers.add_parser("show", help="Show exam details")
    show_parser.add_argument("exam_id", type=int, help="Exam ID")

    # Update exam
    update_parser = subparsers.add_parser("update", help="Update exam")
    update_parser.add_argument("exam_id", type=int, help="Exam ID")
    update_parser.add_argument("--name", help="New name")
    update_parser.add_argument("--exam-type", help="New exam type")
    update_parser.add_argument("--max-points", type=float, help="New max points")
    update_parser.add_argument("--weight", type=float, help="New weight")
    update_parser.add_argument("--course-id", type=int, help="New course ID")
    update_parser.add_argument(
        "--due-date", help="New due date (format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
    )
    update_parser.add_argument(
        "--clear-due-date", action="store_true", help="Clear the due date"
    )

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
                # Parse due_date if provided
                due_date = None
                if args.due_date:
                    try:
                        # Try parsing with time first
                        try:
                            due_date = datetime.strptime(
                                args.due_date, "%Y-%m-%d %H:%M:%S"
                            )
                        except ValueError:
                            # Try parsing date only
                            due_date = datetime.strptime(args.due_date, "%Y-%m-%d")
                    except ValueError:
                        print(
                            f"Error: Invalid date format: {args.due_date}. "
                            "Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                        )
                        return 1

                exam = add_exam(
                    name=args.name,
                    exam_type=args.exam_type,
                    max_points=args.max_points,
                    weight=args.weight,
                    course_id=args.course_id,
                    due_date=due_date,
                )
                if exam:
                    print("\nExam added successfully!")
                    print(f"ID: {exam.id}")
                    print(f"Name: {exam.name}")
                    print(f"Type: {exam.exam_type}")
                    print(f"Max Points: {exam.max_points}")
                    print(f"Weight: {exam.weight * 100}%")
                    print(f"Course: {exam.course.name}")
                    if exam.due_date:
                        print(f"Due Date: {exam.due_date}")
                    return 0
                else:
                    print("Error: Failed to add exam")
                    return 1

            elif args.command == "list":
                exams = list_exams(course_id=args.course_id, exam_type=args.exam_type)
                if not exams:
                    print("No exams found")
                    return 0

                print(f"\nFound {len(exams)} exam(s):\n")
                for exam in exams:
                    print(f"ID {exam.id}: {exam.name}")
                    print(f"  Type: {exam.exam_type}")
                    print(f"  Max Points: {exam.max_points}")
                    print(f"  Weight: {exam.weight * 100}%")
                    print(f"  Course: {exam.course.name}")
                    if exam.due_date:
                        print(f"  Due Date: {exam.due_date}")
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
                print(f"Type: {exam.exam_type}")
                print(f"Max Points: {exam.max_points}")
                print(f"Weight: {exam.weight * 100}%")
                print(f"Course: {exam.course.name}")
                if exam.due_date:
                    print(f"Due Date: {exam.due_date}")
                print(f"Created: {exam.created_at}")
                print(f"Updated: {exam.updated_at}")
                return 0

            elif args.command == "update":
                # Parse due_date if provided
                due_date = None
                if args.due_date:
                    try:
                        # Try parsing with time first
                        try:
                            due_date = datetime.strptime(
                                args.due_date, "%Y-%m-%d %H:%M:%S"
                            )
                        except ValueError:
                            # Try parsing date only
                            due_date = datetime.strptime(args.due_date, "%Y-%m-%d")
                    except ValueError:
                        print(
                            f"Error: Invalid date format: {args.due_date}. "
                            "Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                        )
                        return 1

                exam = update_exam(
                    exam_id=args.exam_id,
                    name=args.name,
                    exam_type=args.exam_type,
                    max_points=args.max_points,
                    weight=args.weight,
                    course_id=args.course_id,
                    due_date=due_date,
                    clear_due_date=args.clear_due_date,
                )
                if exam:
                    print("\nExam updated successfully!")
                    print(f"ID: {exam.id}")
                    print(f"Name: {exam.name}")
                    print(f"Type: {exam.exam_type}")
                    print(f"Max Points: {exam.max_points}")
                    print(f"Weight: {exam.weight * 100}%")
                    print(f"Course: {exam.course.name}")
                    if exam.due_date:
                        print(f"Due Date: {exam.due_date}")
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
                    print(f"Type: {exam.exam_type}")
                    print(f"Course: {exam.course.name}")
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
