"""
Exam management CLI tool.

This module provides command-line interface for managing exam records,
including adding, updating, listing, and deleting exams.

Usage:
    python cli/exam_cli.py add --name "Midterm" --max-points 100 --weight 0.4 --course-id 1
    python cli/exam_cli.py list --course-id 1
    python cli/exam_cli.py show --id 1
    python cli/exam_cli.py update --id 1 --name "Midterm Exam"
    python cli/exam_cli.py delete --id 1
"""

import argparse
import logging
import sys
from datetime import date, datetime
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

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
    max_points: float,
    weight: float,
    course_id: int,
    description: Optional[str] = None,
    exam_date: Optional[date] = None,
    due_date: Optional[date] = None,
) -> Optional[Exam]:
    """
    Add a new exam to the database.

    Args:
        name: Exam name
        max_points: Maximum points achievable (must be positive)
        weight: Weight of exam in final grade (0.0-1.0)
        course_id: Course ID (foreign key)
        description: Optional exam description
        exam_date: Optional date when exam takes place
        due_date: Optional due date for exam submission

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

    # Validate max_points
    if not validate_max_points(max_points):
        raise ValueError(
            f"Invalid max_points: {max_points}. Max points must be positive."
        )

    # Validate weight
    if not validate_weight(weight):
        raise ValueError(
            f"Invalid weight: {weight}. Weight must be between 0.0 and 1.0."
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

    # Validate description length if provided
    if description:
        description = description.strip()
        if len(description) > 5000:
            raise ValueError("Description cannot exceed 5000 characters")

    # Validate dates if provided
    if exam_date and due_date and exam_date > due_date:
        raise ValueError("Exam date cannot be after due date")

    try:
        # Create new exam
        exam = Exam(
            name=name,
            description=description,
            exam_date=exam_date,
            due_date=due_date,
            max_points=max_points,
            weight=weight,
            course_id=course_id,
        )
        app_module.db_session.add(exam)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(
            f"Successfully added exam: {exam.name} "
            f"(max_points={exam.max_points}, weight={exam.weight}) "
            f"for course '{course.name}'"
        )
        return exam

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while adding exam: {e}")
        return None


def list_exams(course_id: Optional[int] = None) -> list[Exam]:
    """
    List all exams with optional filter by course.

    Args:
        course_id: Optional course ID filter

    Returns:
        List of Exam objects matching the filter
    """
    try:
        query = app_module.db_session.query(Exam)  # type: ignore[union-attr]

        if course_id:
            query = query.filter_by(course_id=course_id)

        exams = query.order_by(Exam.course_id, Exam.name).all()

        # Pre-fetch course names to avoid detached instance errors
        for exam in exams:
            _ = exam.course.name  # Access relationship to load it

        return exams

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing exams: {e}")
        return []


def get_exam(exam_id: int) -> Optional[Exam]:
    """
    Get a single exam by ID.

    Args:
        exam_id: Exam ID

    Returns:
        Exam object or None if not found
    """
    try:
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )

        if exam:
            # Pre-fetch course name
            _ = exam.course.name

        return exam

    except SQLAlchemyError as e:
        logger.error(f"Database error while getting exam: {e}")
        return None


def update_exam(
    exam_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    exam_date: Optional[date] = None,
    due_date: Optional[date] = None,
    max_points: Optional[float] = None,
    weight: Optional[float] = None,
) -> Optional[Exam]:
    """
    Update an existing exam.

    Args:
        exam_id: Exam ID to update
        name: New exam name (optional)
        description: New description (optional)
        exam_date: New exam date (optional)
        due_date: New due date (optional)
        max_points: New max points (optional, must be positive)
        weight: New weight (optional, must be 0.0-1.0)

    Returns:
        Updated Exam object or None if failed

    Raises:
        ValueError: If validation fails or exam not found
    """
    try:
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )

        if not exam:
            raise ValueError(f"Exam with ID {exam_id} not found")

        # Update fields if provided
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Exam name cannot be empty")
            if len(name) > 255:
                raise ValueError("Exam name cannot exceed 255 characters")
            exam.name = name

        if description is not None:
            description = description.strip()
            if len(description) > 5000:
                raise ValueError("Description cannot exceed 5000 characters")
            exam.description = description

        if exam_date is not None:
            exam.exam_date = exam_date

        if due_date is not None:
            exam.due_date = due_date

        # Validate dates if both are set
        if exam.exam_date and exam.due_date and exam.exam_date > exam.due_date:
            raise ValueError("Exam date cannot be after due date")

        if max_points is not None:
            if not validate_max_points(max_points):
                raise ValueError(
                    f"Invalid max_points: {max_points}. Max points must be positive."
                )
            exam.max_points = max_points

        if weight is not None:
            if not validate_weight(weight):
                raise ValueError(
                    f"Invalid weight: {weight}. Weight must be between 0.0 and 1.0."
                )
            exam.weight = weight

        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(f"Successfully updated exam: {exam.name} (ID: {exam_id})")
        return exam

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating exam: {e}")
        return None


def delete_exam(exam_id: int) -> bool:
    """
    Delete an exam by ID.

    Args:
        exam_id: Exam ID to delete

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

        logger.info(f"Successfully deleted exam: {exam_name} (ID: {exam_id})")
        return True

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting exam: {e}")
        return False


def main() -> int:
    """
    Main function for CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Initialize Flask app for database access
    app = create_app("development")
    with app.app_context():
        parser = argparse.ArgumentParser(
            description="Exam management CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s add --name "Midterm" --max-points 100 --weight 0.4 --course-id 1
  %(prog)s add --name "Final" --max-points 150 --weight 0.6 --course-id 1 --exam-date 2024-03-15
  %(prog)s list --course-id 1
  %(prog)s show --id 1
  %(prog)s update --id 1 --weight 0.5
  %(prog)s delete --id 1
""",
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Add exam command
        add_parser = subparsers.add_parser("add", help="Add a new exam")
        add_parser.add_argument("--name", required=True, help="Exam name")
        add_parser.add_argument(
            "--max-points",
            type=float,
            required=True,
            help="Maximum points achievable",
        )
        add_parser.add_argument(
            "--weight",
            type=float,
            required=True,
            help="Weight in final grade (0.0-1.0)",
        )
        add_parser.add_argument(
            "--course-id", type=int, required=True, help="Course ID"
        )
        add_parser.add_argument("--description", help="Exam description (optional)")
        add_parser.add_argument(
            "--exam-date", help="Exam date (YYYY-MM-DD, optional)"
        )
        add_parser.add_argument(
            "--due-date", help="Due date (YYYY-MM-DD, optional)"
        )

        # List exams command
        list_parser = subparsers.add_parser("list", help="List exams")
        list_parser.add_argument(
            "--course-id", type=int, help="Filter by course ID (optional)"
        )

        # Show exam command
        show_parser = subparsers.add_parser("show", help="Show exam details")
        show_parser.add_argument("--id", type=int, required=True, help="Exam ID")

        # Update exam command
        update_parser = subparsers.add_parser("update", help="Update an exam")
        update_parser.add_argument("--id", type=int, required=True, help="Exam ID")
        update_parser.add_argument("--name", help="New exam name (optional)")
        update_parser.add_argument(
            "--description", help="New description (optional)"
        )
        update_parser.add_argument(
            "--exam-date", help="New exam date (YYYY-MM-DD, optional)"
        )
        update_parser.add_argument(
            "--due-date", help="New due date (YYYY-MM-DD, optional)"
        )
        update_parser.add_argument(
            "--max-points", type=float, help="New max points (optional)"
        )
        update_parser.add_argument(
            "--weight", type=float, help="New weight (optional)"
        )

        # Delete exam command
        delete_parser = subparsers.add_parser("delete", help="Delete an exam")
        delete_parser.add_argument("--id", type=int, required=True, help="Exam ID")

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return 1

        try:
            if args.command == "add":
                # Parse dates if provided
                exam_date_obj = None
                due_date_obj = None

                if args.exam_date:
                    try:
                        exam_date_obj = datetime.strptime(
                            args.exam_date, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        logger.error(
                            f"Invalid exam date format: {args.exam_date}. "
                            "Use YYYY-MM-DD."
                        )
                        return 1

                if args.due_date:
                    try:
                        due_date_obj = datetime.strptime(
                            args.due_date, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        logger.error(
                            f"Invalid due date format: {args.due_date}. "
                            "Use YYYY-MM-DD."
                        )
                        return 1

                exam = add_exam(
                    name=args.name,
                    max_points=args.max_points,
                    weight=args.weight,
                    course_id=args.course_id,
                    description=args.description,
                    exam_date=exam_date_obj,
                    due_date=due_date_obj,
                )
                if exam:
                    print(f"\nExam added successfully! ID: {exam.id}")
                    print(f"Name: {exam.name}")
                    print(f"Max Points: {exam.max_points}")
                    print(f"Weight: {exam.weight}")
                    print(f"Course: {exam.course.name}")
                    if exam.exam_date:
                        print(f"Exam Date: {exam.exam_date}")
                    if exam.due_date:
                        print(f"Due Date: {exam.due_date}")
                    return 0
                return 1

            elif args.command == "list":
                exams = list_exams(course_id=args.course_id)

                if not exams:
                    print("\nNo exams found.")
                    return 0

                print(f"\nFound {len(exams)} exam(s):\n")
                current_course_id = None
                for exam in exams:
                    if exam.course_id != current_course_id:
                        current_course_id = exam.course_id
                        print(f"\n=== Course: {exam.course.name} ===")

                    print(f"  ID: {exam.id}")
                    print(f"  Name: {exam.name}")
                    print(f"  Max Points: {exam.max_points}")
                    print(f"  Weight: {exam.weight}")
                    if exam.exam_date:
                        print(f"  Exam Date: {exam.exam_date}")
                    if exam.due_date:
                        print(f"  Due Date: {exam.due_date}")
                    print()

                return 0

            elif args.command == "show":
                exam = get_exam(args.id)

                if not exam:
                    logger.error(f"Exam with ID {args.id} not found")
                    return 1

                print("\nExam Details:")
                print(f"  ID: {exam.id}")
                print(f"  Name: {exam.name}")
                print(f"  Description: {exam.description or 'N/A'}")
                print(f"  Max Points: {exam.max_points}")
                print(f"  Weight: {exam.weight}")
                print(f"  Course: {exam.course.name}")
                print(f"  Exam Date: {exam.exam_date or 'Not set'}")
                print(f"  Due Date: {exam.due_date or 'Not set'}")
                print(f"  Created: {exam.created_at}")
                print(f"  Updated: {exam.updated_at}")

                return 0

            elif args.command == "update":
                # Parse dates if provided
                exam_date_obj = None
                due_date_obj = None

                if args.exam_date:
                    try:
                        exam_date_obj = datetime.strptime(
                            args.exam_date, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        logger.error(
                            f"Invalid exam date format: {args.exam_date}. "
                            "Use YYYY-MM-DD."
                        )
                        return 1

                if args.due_date:
                    try:
                        due_date_obj = datetime.strptime(
                            args.due_date, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        logger.error(
                            f"Invalid due date format: {args.due_date}. "
                            "Use YYYY-MM-DD."
                        )
                        return 1

                exam = update_exam(
                    exam_id=args.id,
                    name=args.name,
                    description=args.description,
                    exam_date=exam_date_obj,
                    due_date=due_date_obj,
                    max_points=args.max_points,
                    weight=args.weight,
                )

                if exam:
                    print("\nExam updated successfully!")
                    print(f"  Name: {exam.name}")
                    print(f"  Max Points: {exam.max_points}")
                    print(f"  Weight: {exam.weight}")
                    return 0
                return 1

            elif args.command == "delete":
                if delete_exam(args.id):
                    print("\nExam deleted successfully!")
                    return 0
                return 1

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
