"""
Exam management CLI tool.

This module provides command-line interface for managing exam records,
including adding, updating, listing, and deleting exams and exam components.
"""

import argparse
import logging
import sys
from datetime import date, datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import app as app_module
from app import create_app
from app.models.course import Course
from app.models.exam import Exam, validate_weight, validate_max_points, validate_due_date
from app.models.exam_component import ExamComponent, validate_component_weights_sum

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Exam CRUD Functions
# ============================================================================


def add_exam(
    course_id: int,
    name: str,
    max_points: float,
    weight: float,
    due_date: Optional[str] = None,
) -> Optional[Exam]:
    """
    Add a new exam to the database.

    Args:
        course_id: Course ID (foreign key)
        name: Exam name (e.g., "Final Exam")
        max_points: Maximum points possible (positive number)
        weight: Weight in final grade (0-1 range)
        due_date: Optional due date in ISO format (YYYY-MM-DD)

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
        raise ValueError(f"Max points must be positive, got: {max_points}")

    # Validate weight
    if not validate_weight(weight):
        raise ValueError(f"Weight must be between 0 and 1, got: {weight}")

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

    # Parse and validate due_date if provided
    due_date_obj: Optional[date] = None
    if due_date:
        try:
            due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
            if not validate_due_date(due_date_obj, allow_past=False):
                raise ValueError(f"Due date cannot be in the past: {due_date}")
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError(
                    f"Invalid date format: {due_date}. Use YYYY-MM-DD format"
                ) from e
            raise

    try:
        # Create new exam
        exam = Exam(
            name=name,
            max_points=max_points,
            weight=weight,
            due_date=due_date_obj,
            course_id=course_id,
        )
        app_module.db_session.add(exam)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(
            f"Successfully added exam: {exam.name} for course {course.name} "
            f"(max_points={max_points}, weight={weight})"
        )
        return exam

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while adding exam: {e}")
        return None


def list_exams(course_id: Optional[int] = None) -> list[Exam]:
    """
    List all exams with optional filter.

    Args:
        course_id: Optional course ID filter

    Returns:
        List of Exam objects matching the filter
    """
    try:
        query = app_module.db_session.query(Exam)  # type: ignore[union-attr]

        if course_id:
            query = query.filter_by(course_id=course_id)

        exams = query.order_by(Exam.due_date.desc().nullslast(), Exam.name).all()
        return exams

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing exams: {e}")
        return []


def show_exam(exam_id: int) -> Optional[Exam]:
    """
    Show details of a specific exam.

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
        return exam
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving exam: {e}")
        return None


def update_exam(
    exam_id: int,
    name: Optional[str] = None,
    max_points: Optional[float] = None,
    weight: Optional[float] = None,
    due_date: Optional[str] = None,
) -> Optional[Exam]:
    """
    Update an existing exam.

    Args:
        exam_id: Exam ID
        name: Optional new name
        max_points: Optional new max points
        weight: Optional new weight
        due_date: Optional new due date in ISO format (YYYY-MM-DD)

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

        # Update fields if provided
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Exam name cannot be empty")
            if len(name) > 255:
                raise ValueError("Exam name cannot exceed 255 characters")
            exam.name = name

        if max_points is not None:
            if not validate_max_points(max_points):
                raise ValueError(f"Max points must be positive, got: {max_points}")
            exam.max_points = max_points

        if weight is not None:
            if not validate_weight(weight):
                raise ValueError(f"Weight must be between 0 and 1, got: {weight}")
            exam.weight = weight

        if due_date is not None:
            try:
                due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
                # Allow past dates for updates (exam might have already passed)
                if not validate_due_date(due_date_obj, allow_past=True):
                    raise ValueError(f"Invalid due date: {due_date}")
                exam.due_date = due_date_obj
            except ValueError as e:
                if "does not match format" in str(e):
                    raise ValueError(
                        f"Invalid date format: {due_date}. Use YYYY-MM-DD format"
                    ) from e
                raise

        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(f"Successfully updated exam ID {exam_id}: {exam.name}")
        return exam

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating exam: {e}")
        return None


def delete_exam(exam_id: int, force: bool = False) -> bool:
    """
    Delete an exam from the database.

    Args:
        exam_id: Exam ID to delete
        force: If True, delete without confirmation (for CLI scripts)

    Returns:
        True if deletion was successful, False otherwise

    Raises:
        ValueError: If exam not found or has dependencies
    """
    try:
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )
        if not exam:
            raise ValueError(f"Exam with ID {exam_id} not found")

        # Check for exam components
        if exam.components:
            raise ValueError(
                f"Cannot delete exam '{exam.name}': it has {len(exam.components)} component(s). "
                "Delete components first or use force option."
            )

        exam_name = exam.name
        app_module.db_session.delete(exam)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(f"Successfully deleted exam: {exam_name} (ID: {exam_id})")
        return True

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting exam: {e}")
        return False


# ============================================================================
# Exam Component CRUD Functions
# ============================================================================


def add_exam_component(
    exam_id: int,
    name: str,
    max_points: float,
    weight: float,
    order: int = 1,
) -> Optional[ExamComponent]:
    """
    Add a new exam component to the database.

    Args:
        exam_id: Exam ID (foreign key)
        name: Component name (e.g., "Multiple Choice")
        max_points: Maximum points for this component (positive number)
        weight: Weight within the exam (0-1 range)
        order: Display order (default: 1)

    Returns:
        Created ExamComponent object or None if failed

    Raises:
        ValueError: If validation fails
        IntegrityError: If component with same exam_id+order already exists
    """
    # Validate name
    if not name or not name.strip():
        raise ValueError("Component name cannot be empty")

    name = name.strip()
    if len(name) > 255:
        raise ValueError("Component name cannot exceed 255 characters")

    # Validate max_points
    if not validate_max_points(max_points):
        raise ValueError(f"Max points must be positive, got: {max_points}")

    # Validate weight
    if not validate_weight(weight):
        raise ValueError(f"Weight must be between 0 and 1, got: {weight}")

    # Validate order
    if order < 1:
        raise ValueError(f"Order must be at least 1, got: {order}")

    # Validate exam exists
    try:
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )
        if not exam:
            raise ValueError(f"Exam with ID {exam_id} not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error while checking exam: {e}")
        raise ValueError(f"Error checking exam: {e}") from e

    try:
        # Create new component
        component = ExamComponent(
            name=name,
            max_points=max_points,
            weight=weight,
            order=order,
            exam_id=exam_id,
        )
        app_module.db_session.add(component)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(
            f"Successfully added exam component: {component.name} for exam {exam.name} "
            f"(max_points={max_points}, weight={weight}, order={order})"
        )
        return component

    except IntegrityError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        error_msg = str(e)
        if "uq_exam_component_exam_order" in error_msg.lower():
            raise IntegrityError(
                f"Component with order {order} already exists for exam '{exam.name}'",
                params=None,
                orig=e.orig,  # type: ignore[arg-type]
            ) from e
        raise

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while adding exam component: {e}")
        return None


def list_exam_components(exam_id: int) -> list[ExamComponent]:
    """
    List all components for a specific exam.

    Args:
        exam_id: Exam ID filter

    Returns:
        List of ExamComponent objects ordered by order field
    """
    try:
        components = (
            app_module.db_session.query(ExamComponent)  # type: ignore[union-attr]
            .filter_by(exam_id=exam_id)
            .order_by(ExamComponent.order)
            .all()
        )
        return components

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing exam components: {e}")
        return []


def update_exam_component(
    component_id: int,
    name: Optional[str] = None,
    max_points: Optional[float] = None,
    weight: Optional[float] = None,
    order: Optional[int] = None,
) -> Optional[ExamComponent]:
    """
    Update an existing exam component.

    Args:
        component_id: Component ID
        name: Optional new name
        max_points: Optional new max points
        weight: Optional new weight
        order: Optional new order

    Returns:
        Updated ExamComponent object or None if failed

    Raises:
        ValueError: If validation fails
    """
    try:
        component = (
            app_module.db_session.query(ExamComponent)  # type: ignore[union-attr]
            .filter_by(id=component_id)
            .first()
        )
        if not component:
            raise ValueError(f"Exam component with ID {component_id} not found")

        # Update fields if provided
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Component name cannot be empty")
            if len(name) > 255:
                raise ValueError("Component name cannot exceed 255 characters")
            component.name = name

        if max_points is not None:
            if not validate_max_points(max_points):
                raise ValueError(f"Max points must be positive, got: {max_points}")
            component.max_points = max_points

        if weight is not None:
            if not validate_weight(weight):
                raise ValueError(f"Weight must be between 0 and 1, got: {weight}")
            component.weight = weight

        if order is not None:
            if order < 1:
                raise ValueError(f"Order must be at least 1, got: {order}")
            component.order = order

        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(
            f"Successfully updated exam component ID {component_id}: {component.name}"
        )
        return component

    except IntegrityError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        if "uq_exam_component_exam_order" in str(e).lower():
            raise ValueError(
                f"Component with order {order} already exists for this exam"
            ) from e
        raise

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating exam component: {e}")
        return None


def delete_exam_component(component_id: int) -> bool:
    """
    Delete an exam component from the database.

    Args:
        component_id: Component ID to delete

    Returns:
        True if deletion was successful, False otherwise

    Raises:
        ValueError: If component not found
    """
    try:
        component = (
            app_module.db_session.query(ExamComponent)  # type: ignore[union-attr]
            .filter_by(id=component_id)
            .first()
        )
        if not component:
            raise ValueError(f"Exam component with ID {component_id} not found")

        component_name = component.name
        app_module.db_session.delete(component)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(
            f"Successfully deleted exam component: {component_name} (ID: {component_id})"
        )
        return True

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting exam component: {e}")
        return False


def validate_exam_component_weights(exam_id: int) -> tuple[bool, float]:
    """
    Validate that component weights sum to approximately 1.0 for an exam.

    Args:
        exam_id: Exam ID to check

    Returns:
        Tuple of (is_valid, total_weight)
    """
    try:
        components = list_exam_components(exam_id)
        if not components:
            return (True, 0.0)

        total_weight = sum(comp.weight for comp in components)
        is_valid = validate_component_weights_sum(components)
        return (is_valid, total_weight)

    except SQLAlchemyError as e:
        logger.error(f"Database error while validating component weights: {e}")
        return (False, 0.0)


# ============================================================================
# CLI Interface
# ============================================================================


def main() -> int:
    """
    Main entry point for the exam CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(description="Exam Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # === Exam Commands ===

    # exam add
    exam_add = subparsers.add_parser("exam-add", help="Add a new exam")
    exam_add.add_argument("--course-id", type=int, required=True, help="Course ID")
    exam_add.add_argument("--name", type=str, required=True, help="Exam name")
    exam_add.add_argument(
        "--max-points", type=float, required=True, help="Maximum points"
    )
    exam_add.add_argument(
        "--weight",
        type=float,
        required=True,
        help="Weight in final grade (0-1 range)",
    )
    exam_add.add_argument(
        "--due-date", type=str, help="Due date in YYYY-MM-DD format"
    )

    # exam list
    exam_list = subparsers.add_parser("exam-list", help="List exams")
    exam_list.add_argument("--course-id", type=int, help="Filter by course ID")

    # exam show
    exam_show = subparsers.add_parser("exam-show", help="Show exam details")
    exam_show.add_argument("exam_id", type=int, help="Exam ID")

    # exam update
    exam_update = subparsers.add_parser("exam-update", help="Update an exam")
    exam_update.add_argument("exam_id", type=int, help="Exam ID")
    exam_update.add_argument("--name", type=str, help="New name")
    exam_update.add_argument("--max-points", type=float, help="New maximum points")
    exam_update.add_argument("--weight", type=float, help="New weight")
    exam_update.add_argument(
        "--due-date", type=str, help="New due date in YYYY-MM-DD format"
    )

    # exam delete
    exam_delete = subparsers.add_parser("exam-delete", help="Delete an exam")
    exam_delete.add_argument("exam_id", type=int, help="Exam ID")
    exam_delete.add_argument(
        "--force", action="store_true", help="Force delete without confirmation"
    )

    # === Exam Component Commands ===

    # component add
    comp_add = subparsers.add_parser("component-add", help="Add a new exam component")
    comp_add.add_argument("--exam-id", type=int, required=True, help="Exam ID")
    comp_add.add_argument("--name", type=str, required=True, help="Component name")
    comp_add.add_argument(
        "--max-points", type=float, required=True, help="Maximum points"
    )
    comp_add.add_argument(
        "--weight", type=float, required=True, help="Weight within exam (0-1 range)"
    )
    comp_add.add_argument("--order", type=int, default=1, help="Display order")

    # component list
    comp_list = subparsers.add_parser("component-list", help="List exam components")
    comp_list.add_argument("--exam-id", type=int, required=True, help="Exam ID")

    # component update
    comp_update = subparsers.add_parser(
        "component-update", help="Update an exam component"
    )
    comp_update.add_argument("component_id", type=int, help="Component ID")
    comp_update.add_argument("--name", type=str, help="New name")
    comp_update.add_argument("--max-points", type=float, help="New maximum points")
    comp_update.add_argument("--weight", type=float, help="New weight")
    comp_update.add_argument("--order", type=int, help="New order")

    # component delete
    comp_delete = subparsers.add_parser(
        "component-delete", help="Delete an exam component"
    )
    comp_delete.add_argument("component_id", type=int, help="Component ID")

    # component validate
    comp_validate = subparsers.add_parser(
        "component-validate", help="Validate exam component weights"
    )
    comp_validate.add_argument("--exam-id", type=int, required=True, help="Exam ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize Flask app to get database session
    app = create_app("development")
    with app.app_context():
        try:
            # === Execute Exam Commands ===
            if args.command == "exam-add":
                exam = add_exam(
                    course_id=args.course_id,
                    name=args.name,
                    max_points=args.max_points,
                    weight=args.weight,
                    due_date=args.due_date,
                )
                if exam:
                    print(f"Successfully added exam: {exam.name} (ID: {exam.id})")
                    return 0
                else:
                    print("Failed to add exam", file=sys.stderr)
                    return 1

            elif args.command == "exam-list":
                exams = list_exams(course_id=args.course_id)
                if not exams:
                    print("No exams found")
                else:
                    print(f"\n{'ID':<5} {'Name':<30} {'Max Points':<12} {'Weight':<8} {'Due Date':<12} {'Course ID':<10}")
                    print("-" * 85)
                    for exam in exams:
                        due_date_str = exam.due_date.isoformat() if exam.due_date else "N/A"
                        print(
                            f"{exam.id:<5} {exam.name:<30} {exam.max_points:<12.1f} {exam.weight:<8.2f} {due_date_str:<12} {exam.course_id:<10}"
                        )
                return 0

            elif args.command == "exam-show":
                exam = show_exam(args.exam_id)
                if exam:
                    print("\nExam Details:")
                    print(f"  ID: {exam.id}")
                    print(f"  Name: {exam.name}")
                    print(f"  Max Points: {exam.max_points}")
                    print(f"  Weight: {exam.weight}")
                    print(f"  Due Date: {exam.due_date.isoformat() if exam.due_date else 'N/A'}")
                    print(f"  Course ID: {exam.course_id}")
                    print(f"  Components: {len(exam.components)}")
                    return 0
                else:
                    print(f"Exam with ID {args.exam_id} not found", file=sys.stderr)
                    return 1

            elif args.command == "exam-update":
                exam = update_exam(
                    exam_id=args.exam_id,
                    name=args.name,
                    max_points=args.max_points,
                    weight=args.weight,
                    due_date=args.due_date,
                )
                if exam:
                    print(f"Successfully updated exam ID {exam.id}: {exam.name}")
                    return 0
                else:
                    print("Failed to update exam", file=sys.stderr)
                    return 1

            elif args.command == "exam-delete":
                if delete_exam(args.exam_id, force=args.force):
                    print(f"Successfully deleted exam ID {args.exam_id}")
                    return 0
                else:
                    print("Failed to delete exam", file=sys.stderr)
                    return 1

            # === Execute Component Commands ===
            elif args.command == "component-add":
                component = add_exam_component(
                    exam_id=args.exam_id,
                    name=args.name,
                    max_points=args.max_points,
                    weight=args.weight,
                    order=args.order,
                )
                if component:
                    print(
                        f"Successfully added component: {component.name} (ID: {component.id})"
                    )
                    return 0
                else:
                    print("Failed to add component", file=sys.stderr)
                    return 1

            elif args.command == "component-list":
                components = list_exam_components(exam_id=args.exam_id)
                if not components:
                    print(f"No components found for exam ID {args.exam_id}")
                else:
                    print(f"\n{'ID':<5} {'Order':<7} {'Name':<30} {'Max Points':<12} {'Weight':<8}")
                    print("-" * 70)
                    for comp in components:
                        print(
                            f"{comp.id:<5} {comp.order:<7} {comp.name:<30} {comp.max_points:<12.1f} {comp.weight:<8.2f}"
                        )
                return 0

            elif args.command == "component-update":
                component = update_exam_component(
                    component_id=args.component_id,
                    name=args.name,
                    max_points=args.max_points,
                    weight=args.weight,
                    order=args.order,
                )
                if component:
                    print(
                        f"Successfully updated component ID {component.id}: {component.name}"
                    )
                    return 0
                else:
                    print("Failed to update component", file=sys.stderr)
                    return 1

            elif args.command == "component-delete":
                if delete_exam_component(args.component_id):
                    print(f"Successfully deleted component ID {args.component_id}")
                    return 0
                else:
                    print("Failed to delete component", file=sys.stderr)
                    return 1

            elif args.command == "component-validate":
                is_valid, total_weight = validate_exam_component_weights(args.exam_id)
                print(f"\nComponent weight validation for exam ID {args.exam_id}:")
                print(f"  Total weight: {total_weight:.3f}")
                print(f"  Valid (≈1.0): {'Yes' if is_valid else 'No'}")
                if not is_valid and total_weight > 0:
                    print("  Warning: Component weights should sum to 1.0")
                return 0 if is_valid else 1

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            logger.exception("Unexpected error in exam CLI")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
