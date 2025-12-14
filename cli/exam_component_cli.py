"""
Exam component management CLI tool.

This module provides command-line interface for managing exam components,
including adding, updating, listing, and deleting components with weight validation.
"""

import argparse
import logging
import sys
from typing import Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import app as app_module
from app import create_app
from app.models.exam import Exam
from app.models.exam_component import (
    ExamComponent,
    validate_weight,
    validate_max_points,
    validate_order,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_total_weight(
    exam_id: int, exclude_component_id: Optional[int] = None
) -> tuple[bool, float]:
    """
    Validate that total weight of all components for an exam equals 1.0.

    Args:
        exam_id: Exam database ID
        exclude_component_id: Optional component ID to exclude from calculation
                             (useful when updating a component)

    Returns:
        Tuple of (is_valid, current_total_weight)
    """
    try:
        query = app_module.db_session.query(ExamComponent).filter_by(exam_id=exam_id)  # type: ignore[union-attr]

        if exclude_component_id:
            query = query.filter(ExamComponent.id != exclude_component_id)

        components = query.all()
        total_weight = float(sum(c.weight for c in components))

        # Allow small floating point tolerance (0.001)
        is_valid = abs(total_weight - 1.0) < 0.001

        return (is_valid, total_weight)

    except SQLAlchemyError as e:
        logger.error(f"Database error while validating total weight: {e}")
        return (False, 0.0)


def get_available_weight(
    exam_id: int, exclude_component_id: Optional[int] = None
) -> float:
    """
    Get available weight remaining for an exam.

    Args:
        exam_id: Exam database ID
        exclude_component_id: Optional component ID to exclude from calculation

    Returns:
        Available weight (1.0 - sum of existing weights)
    """
    _, current_total = validate_total_weight(exam_id, exclude_component_id)
    return 1.0 - current_total


def add_component(
    name: str,
    max_points: float,
    weight: float,
    exam_id: int,
    description: Optional[str] = None,
    order: int = 0,
) -> Optional[ExamComponent]:
    """
    Add a new exam component to the database.

    Args:
        name: Component name (e.g., "Written Part", "Practical Exam")
        max_points: Maximum points achievable (must be positive)
        weight: Weight in exam grade (0-1, e.g., 0.4 = 40%)
        exam_id: Exam ID (foreign key)
        description: Optional description
        order: Display order (default: 0)

    Returns:
        Created ExamComponent object or None if failed

    Raises:
        ValueError: If validation fails
        IntegrityError: If database constraint is violated
    """
    # Validate name
    if not name or not name.strip():
        raise ValueError("Component name cannot be empty")

    name = name.strip()
    if len(name) > 255:
        raise ValueError("Component name cannot exceed 255 characters")

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
            "Weight must be between 0 and 1 (e.g., 0.4 for 40%)."
        )

    # Validate order
    if not validate_order(order):
        raise ValueError(
            f"Invalid order: {order}. Order must be a non-negative integer."
        )

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

    # Check total weight constraint
    available_weight = get_available_weight(exam_id)
    if weight > available_weight + 0.001:  # Small tolerance for floating point
        raise ValueError(
            f"Invalid weight: {weight}. "
            f"Only {available_weight:.3f} weight available for exam '{exam.name}'. "
            f"Total weight of all components must equal 1.0."
        )

    try:
        # Create new component
        component = ExamComponent(
            name=name,
            max_points=max_points,
            weight=weight,
            exam_id=exam_id,
            description=description,
            order=order,
        )
        app_module.db_session.add(component)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(
            f"Successfully added component: {component.name} for exam {exam.name}"
        )
        return component

    except IntegrityError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database integrity error while adding component: {e}")
        raise

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while adding component: {e}")
        return None


def list_components(exam_id: Optional[int] = None) -> list[ExamComponent]:
    """
    List all exam components with optional filter.

    Args:
        exam_id: Optional exam ID filter

    Returns:
        List of ExamComponent objects matching the filters, ordered by exam_id and order
    """
    try:
        query = app_module.db_session.query(ExamComponent)  # type: ignore[union-attr]

        if exam_id:
            query = query.filter_by(exam_id=exam_id)

        components = query.order_by(ExamComponent.exam_id, ExamComponent.order).all()
        return components

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing components: {e}")
        return []


def get_component(component_id: int) -> Optional[ExamComponent]:
    """
    Get an exam component by ID.

    Args:
        component_id: ExamComponent database ID

    Returns:
        ExamComponent object or None if not found
    """
    try:
        component = (
            app_module.db_session.query(ExamComponent)  # type: ignore[union-attr]
            .filter_by(id=component_id)
            .first()
        )
        return component

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching component: {e}")
        return None


def update_component(
    component_id: int,
    name: Optional[str] = None,
    max_points: Optional[float] = None,
    weight: Optional[float] = None,
    description: Optional[str] = None,
    order: Optional[int] = None,
) -> Optional[ExamComponent]:
    """
    Update an existing exam component.

    Args:
        component_id: ExamComponent database ID
        name: Optional new name
        max_points: Optional new max_points
        weight: Optional new weight
        description: Optional new description
        order: Optional new order

    Returns:
        Updated ExamComponent object or None if failed

    Raises:
        ValueError: If validation fails
        IntegrityError: If update would violate database constraint
    """
    try:
        component = (
            app_module.db_session.query(ExamComponent)  # type: ignore[union-attr]
            .filter_by(id=component_id)
            .first()
        )

        if not component:
            raise ValueError(f"Component with ID {component_id} not found")

        # Update name
        if name:
            name = name.strip()
            if not name:
                raise ValueError("Component name cannot be empty")
            if len(name) > 255:
                raise ValueError("Component name cannot exceed 255 characters")
            component.name = name

        # Update max_points
        if max_points is not None:
            if not validate_max_points(max_points):
                raise ValueError(
                    f"Invalid max_points: {max_points}. "
                    "Maximum points must be a positive number."
                )
            component.max_points = max_points

        # Update weight with total weight validation
        if weight is not None:
            if not validate_weight(weight):
                raise ValueError(
                    f"Invalid weight: {weight}. "
                    "Weight must be between 0 and 1 (e.g., 0.4 for 40%)."
                )

            # Check total weight constraint (excluding this component)
            available_weight = get_available_weight(
                int(component.exam_id), int(component.id)
            )
            if weight > available_weight + 0.001:
                raise ValueError(
                    f"Invalid weight: {weight}. "
                    f"Only {available_weight:.3f} weight available. "
                    f"Total weight of all components must equal 1.0."
                )
            component.weight = weight

        # Update description
        if description is not None:
            component.description = description

        # Update order
        if order is not None:
            if not validate_order(order):
                raise ValueError(
                    f"Invalid order: {order}. Order must be a non-negative integer."
                )
            component.order = order

        app_module.db_session.commit()  # type: ignore[union-attr]
        logger.info(f"Successfully updated component: {component.name}")
        return component

    except IntegrityError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database integrity error while updating component: {e}")
        raise

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating component: {e}")
        return None


def delete_component(component_id: int) -> bool:
    """
    Delete an exam component from the database.

    Args:
        component_id: ExamComponent database ID

    Returns:
        True if deleted successfully, False otherwise

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
            raise ValueError(f"Component with ID {component_id} not found")

        component_name = component.name
        app_module.db_session.delete(component)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        logger.info(f"Successfully deleted component: {component_name}")
        return True

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting component: {e}")
        return False


def reorder_component(component_id: int, new_order: int) -> Optional[ExamComponent]:
    """
    Change the order of an exam component.

    Args:
        component_id: ExamComponent database ID
        new_order: New order value

    Returns:
        Updated ExamComponent object or None if failed

    Raises:
        ValueError: If validation fails
    """
    return update_component(component_id, order=new_order)


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Exam Component Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add component
    add_parser = subparsers.add_parser("add", help="Add a new exam component")
    add_parser.add_argument("--name", required=True, help="Component name")
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
        help="Weight in exam grade (0-1, e.g., 0.4 for 40%%)",
    )
    add_parser.add_argument("--exam-id", type=int, required=True, help="Exam ID")
    add_parser.add_argument("--description", help="Optional description")
    add_parser.add_argument(
        "--order", type=int, default=0, help="Display order (default: 0)"
    )

    # List components
    list_parser = subparsers.add_parser("list", help="List exam components")
    list_parser.add_argument("--exam-id", type=int, help="Filter by exam ID")

    # Show component details
    show_parser = subparsers.add_parser("show", help="Show component details")
    show_parser.add_argument("component_id", type=int, help="Component ID")

    # Update component
    update_parser = subparsers.add_parser("update", help="Update component")
    update_parser.add_argument("component_id", type=int, help="Component ID")
    update_parser.add_argument("--name", help="New name")
    update_parser.add_argument("--max-points", type=float, help="New max points")
    update_parser.add_argument("--weight", type=float, help="New weight")
    update_parser.add_argument("--description", help="New description")
    update_parser.add_argument("--order", type=int, help="New order")

    # Delete component
    delete_parser = subparsers.add_parser("delete", help="Delete component")
    delete_parser.add_argument("component_id", type=int, help="Component ID")
    delete_parser.add_argument("--yes", action="store_true", help="Skip confirmation")

    # Reorder component
    reorder_parser = subparsers.add_parser("reorder", help="Change component order")
    reorder_parser.add_argument("component_id", type=int, help="Component ID")
    reorder_parser.add_argument("new_order", type=int, help="New order value")

    # Check weights
    check_parser = subparsers.add_parser(
        "check-weights", help="Check total weight for an exam"
    )
    check_parser.add_argument("exam_id", type=int, help="Exam ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create app and initialize database connection
    app = create_app()
    with app.app_context():
        try:
            if args.command == "add":
                component = add_component(
                    name=args.name,
                    max_points=args.max_points,
                    weight=args.weight,
                    exam_id=args.exam_id,
                    description=args.description,
                    order=args.order,
                )
                if component:
                    print("\nComponent added successfully!")
                    print(f"ID: {component.id}")
                    print(f"Name: {component.name}")
                    print(f"Max Points: {component.max_points}")
                    print(f"Weight: {component.weight * 100}%")
                    print(f"Order: {component.order}")
                    print(f"Exam: {component.exam.name}")
                    return 0
                else:
                    print("Error: Failed to add component")
                    return 1

            elif args.command == "list":
                components = list_components(exam_id=args.exam_id)
                if not components:
                    print("No components found")
                    return 0

                print(f"\nFound {len(components)} component(s):\n")

                current_exam_id: Optional[int] = None
                for component in components:
                    if component.exam_id != current_exam_id:
                        current_exam_id = int(component.exam_id)
                        print(f"\n=== Exam: {component.exam.name} ===")
                        is_valid, total = validate_total_weight(current_exam_id)
                        print(
                            f"Total Weight: {total:.3f} {'✓' if is_valid else '✗ (should be 1.0)'}\n"
                        )

                    print(f"  [{component.order}] ID {component.id}: {component.name}")
                    print(f"      Max Points: {component.max_points}")
                    print(f"      Weight: {component.weight * 100}%")
                    if component.description:
                        print(f"      Description: {component.description}")
                    print()

                return 0

            elif args.command == "show":
                component = get_component(args.component_id)
                if not component:
                    print(f"Error: Component with ID {args.component_id} not found")
                    return 1

                print("\nComponent Details:")
                print(f"ID: {component.id}")
                print(f"Name: {component.name}")
                print(f"Max Points: {component.max_points}")
                print(f"Weight: {component.weight * 100}%")
                print(f"Order: {component.order}")
                print(f"Exam: {component.exam.name}")
                if component.description:
                    print(f"Description: {component.description}")
                print(f"Created: {component.created_at}")
                print(f"Updated: {component.updated_at}")
                return 0

            elif args.command == "update":
                component = update_component(
                    component_id=args.component_id,
                    name=args.name,
                    max_points=args.max_points,
                    weight=args.weight,
                    description=args.description,
                    order=args.order,
                )
                if component:
                    print("\nComponent updated successfully!")
                    print(f"ID: {component.id}")
                    print(f"Name: {component.name}")
                    print(f"Max Points: {component.max_points}")
                    print(f"Weight: {component.weight * 100}%")
                    print(f"Order: {component.order}")
                    return 0
                else:
                    print("Error: Failed to update component")
                    return 1

            elif args.command == "delete":
                component = get_component(args.component_id)
                if not component:
                    print(f"Error: Component with ID {args.component_id} not found")
                    return 1

                if not args.yes:
                    print("\nAre you sure you want to delete this component?")
                    print(f"Name: {component.name}")
                    print(f"Exam: {component.exam.name}")
                    response = input("\nType 'yes' to confirm: ")
                    if response.lower() != "yes":
                        print("Deletion cancelled")
                        return 0

                if delete_component(args.component_id):
                    print("Component deleted successfully")
                    return 0
                else:
                    print("Error: Failed to delete component")
                    return 1

            elif args.command == "reorder":
                component = reorder_component(args.component_id, args.new_order)
                if component:
                    print(
                        f"Component '{component.name}' order updated to {args.new_order}"
                    )
                    return 0
                else:
                    print("Error: Failed to update component order")
                    return 1

            elif args.command == "check-weights":
                exam = (
                    app_module.db_session.query(Exam)  # type: ignore[union-attr]
                    .filter_by(id=args.exam_id)
                    .first()
                )
                if not exam:
                    print(f"Error: Exam with ID {args.exam_id} not found")
                    return 1

                components = list_components(exam_id=args.exam_id)
                if not components:
                    print(f"No components found for exam '{exam.name}'")
                    return 0

                print(f"\n=== Weight Check for Exam: {exam.name} ===\n")

                total_weight = 0.0
                for component in components:
                    print(f"  {component.name}: {component.weight * 100}%")
                    total_weight += float(component.weight)

                print(f"\n  Total: {total_weight * 100}%")

                is_valid = abs(total_weight - 1.0) < 0.001
                if is_valid:
                    print("  Status: ✓ Valid (equals 1.0)")
                else:
                    print(
                        f"  Status: ✗ Invalid (should be 100%, is {total_weight * 100}%)"
                    )
                    print(f"  Difference: {(1.0 - total_weight) * 100:+.1f}%")

                return 0 if is_valid else 1

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
