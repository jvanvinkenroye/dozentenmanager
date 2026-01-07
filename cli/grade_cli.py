"""
Grade management CLI tool.

This module provides command-line interface for managing grades,
including adding grades, calculating weighted averages, and
managing grading scales.
"""

import argparse
import logging
import sys

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import create_app, db
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.exam_component import ExamComponent
from app.models.grade import (
    GERMAN_GRADES,
    Grade,
    GradeThreshold,
    GradingScale,
    calculate_percentage,
    percentage_to_german_grade,
    validate_points,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def add_grade(
    enrollment_id: int,
    exam_id: int,
    points: float,
    component_id: int | None = None,
    graded_by: str | None = None,
    is_final: bool = False,
    notes: str | None = None,
) -> Grade | None:
    """
    Add a grade for a student's exam/component.

    Args:
        enrollment_id: Enrollment ID
        exam_id: Exam ID
        points: Points achieved
        component_id: Optional component ID for multi-part exams
        graded_by: Who assigned the grade
        is_final: Whether this is the final grade
        notes: Optional notes

    Returns:
        Created Grade object or None if failed

    Raises:
        ValueError: If validation fails
    """
    # Validate enrollment exists
    enrollment = db.session.query(Enrollment).filter_by(id=enrollment_id).first()
    if not enrollment:
        raise ValueError(f"Enrollment with ID {enrollment_id} not found")

    # Validate exam exists
    exam = db.session.query(Exam).filter_by(id=exam_id).first()
    if not exam:
        raise ValueError(f"Exam with ID {exam_id} not found")

    # Get max points from component or exam
    if component_id:
        component = db.session.query(ExamComponent).filter_by(id=component_id).first()
        if not component:
            raise ValueError(f"ExamComponent with ID {component_id} not found")
        if component.exam_id != exam_id:
            raise ValueError(f"Component {component_id} does not belong to exam {exam_id}")
        max_points = component.max_points
    else:
        max_points = exam.max_points

    # Validate points
    if not validate_points(points, max_points):
        raise ValueError(f"Points must be between 0 and {max_points}")

    # Check for existing grade
    existing = db.session.query(Grade).filter_by(
        enrollment_id=enrollment_id,
        exam_id=exam_id,
        component_id=component_id,
    ).first()
    if existing:
        raise ValueError(
            "Grade already exists for this enrollment/exam/component combination. "
            "Use update_grade to modify."
        )

    try:
        grade = Grade.create_with_auto_grade(
            enrollment_id=enrollment_id,
            exam_id=exam_id,
            points=points,
            max_points=max_points,
            component_id=component_id,
            graded_by=graded_by,
            is_final=is_final,
            notes=notes,
        )
        db.session.add(grade)
        db.session.commit()

        logger.info(
            f"Grade added: {grade.points}/{max_points} = {grade.percentage}% "
            f"({grade.grade_value} - {grade.grade_label})"
        )
        return grade

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while adding grade: {e}")
        return None


def update_grade(
    grade_id: int,
    points: float | None = None,
    is_final: bool | None = None,
    notes: str | None = None,
    graded_by: str | None = None,
) -> Grade | None:
    """
    Update an existing grade.

    Args:
        grade_id: Grade ID to update
        points: New points (will recalculate percentage and grade)
        is_final: New final status
        notes: New notes
        graded_by: Who updated the grade

    Returns:
        Updated Grade object or None if failed

    Raises:
        ValueError: If validation fails
    """
    grade = db.session.query(Grade).filter_by(id=grade_id).first()
    if not grade:
        raise ValueError(f"Grade with ID {grade_id} not found")

    try:
        if points is not None:
            # Get max points
            if grade.component_id:
                component = db.session.query(ExamComponent).filter_by(
                    id=grade.component_id
                ).first()
                max_points = component.max_points
            else:
                exam = db.session.query(Exam).filter_by(id=grade.exam_id).first()
                max_points = exam.max_points

            if not validate_points(points, max_points):
                raise ValueError(f"Points must be between 0 and {max_points}")

            grade.points = points
            grade.percentage = calculate_percentage(points, max_points)
            grade.grade_value, grade.grade_label = percentage_to_german_grade(
                grade.percentage
            )

        if is_final is not None:
            grade.is_final = is_final

        if notes is not None:
            grade.notes = notes

        if graded_by is not None:
            grade.graded_by = graded_by

        db.session.commit()
        logger.info(f"Grade {grade_id} updated successfully")
        return grade

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while updating grade: {e}")
        return None


def delete_grade(grade_id: int) -> bool:
    """
    Delete a grade.

    Args:
        grade_id: Grade ID to delete

    Returns:
        True if deleted, False otherwise

    Raises:
        ValueError: If grade not found
    """
    grade = db.session.query(Grade).filter_by(id=grade_id).first()
    if not grade:
        raise ValueError(f"Grade with ID {grade_id} not found")

    try:
        db.session.delete(grade)
        db.session.commit()
        logger.info(f"Grade {grade_id} deleted")
        return True

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while deleting grade: {e}")
        return False


def get_grade(grade_id: int) -> Grade | None:
    """Get a grade by ID."""
    return db.session.query(Grade).filter_by(id=grade_id).first()


def list_grades(
    enrollment_id: int | None = None,
    exam_id: int | None = None,
    course_id: int | None = None,
    is_final: bool | None = None,
) -> list[Grade]:
    """
    List grades with optional filters.

    Args:
        enrollment_id: Filter by enrollment
        exam_id: Filter by exam
        course_id: Filter by course (through enrollment)
        is_final: Filter by final status

    Returns:
        List of matching Grade objects
    """
    query = db.session.query(Grade)

    if enrollment_id:
        query = query.filter(Grade.enrollment_id == enrollment_id)

    if exam_id:
        query = query.filter(Grade.exam_id == exam_id)

    if course_id:
        query = query.join(Enrollment).filter(Enrollment.course_id == course_id)

    if is_final is not None:
        query = query.filter(Grade.is_final == is_final)

    return query.order_by(Grade.graded_at.desc()).all()


def calculate_weighted_average(
    enrollment_id: int, course_id: int | None = None
) -> dict | None:
    """
    Calculate weighted average grade for an enrollment.

    For multi-part exams, uses component weights.
    For regular exams, uses exam weights.

    Args:
        enrollment_id: Enrollment ID
        course_id: Optional course ID filter

    Returns:
        Dictionary with weighted average info or None if no grades
    """
    enrollment = db.session.query(Enrollment).filter_by(id=enrollment_id).first()
    if not enrollment:
        return None

    # Get all final grades for the enrollment
    query = db.session.query(Grade).filter(
        Grade.enrollment_id == enrollment_id,
        Grade.is_final == True,  # noqa: E712
    )

    if course_id:
        query = query.join(Exam).filter(Exam.course_id == course_id)

    grades = query.all()

    if not grades:
        return None

    total_weight = 0.0
    weighted_sum = 0.0
    exam_grades = {}

    for grade in grades:
        exam = grade.exam

        if grade.component_id:
            # Multi-part exam - use component weight
            component = grade.component
            weight = (component.weight / 100) * (exam.weight / 100)
        else:
            # Regular exam - use exam weight
            weight = exam.weight / 100

        weighted_sum += grade.grade_value * weight
        total_weight += weight

        # Track per-exam grades
        if exam.id not in exam_grades:
            exam_grades[exam.id] = {
                "exam_name": exam.name,
                "exam_weight": exam.weight,
                "components": [],
                "final_grade": None,
            }

        if grade.component_id:
            exam_grades[exam.id]["components"].append({
                "component_name": grade.component.name,
                "points": grade.points,
                "percentage": grade.percentage,
                "grade": grade.grade_value,
            })
        else:
            exam_grades[exam.id]["final_grade"] = {
                "points": grade.points,
                "percentage": grade.percentage,
                "grade": grade.grade_value,
            }

    if total_weight == 0:
        return None

    weighted_average = weighted_sum / total_weight

    # Determine final grade label
    _, grade_label = percentage_to_german_grade(
        100 - ((weighted_average - 1) * 25)  # Approximate reverse
    )

    return {
        "enrollment_id": enrollment_id,
        "student_name": f"{enrollment.student.last_name}, {enrollment.student.first_name}",
        "weighted_average": round(weighted_average, 2),
        "grade_label": grade_label,
        "total_weight": round(total_weight * 100, 1),
        "exam_grades": exam_grades,
        "is_passing": weighted_average <= 4.0,
    }


def get_exam_statistics(exam_id: int) -> dict | None:
    """
    Calculate statistics for an exam.

    Args:
        exam_id: Exam ID

    Returns:
        Dictionary with statistics or None if no grades
    """
    exam = db.session.query(Exam).filter_by(id=exam_id).first()
    if not exam:
        return None

    grades = db.session.query(Grade).filter(
        Grade.exam_id == exam_id,
        Grade.component_id == None,  # noqa: E711 - Only exam-level grades
    ).all()

    if not grades:
        return None

    points_list = [g.points for g in grades]
    percentage_list = [g.percentage for g in grades]
    grade_values = [g.grade_value for g in grades]

    # Count grade distribution
    grade_distribution = {}
    for g in grades:
        label = g.grade_label
        grade_distribution[label] = grade_distribution.get(label, 0) + 1

    passing_count = sum(1 for g in grades if g.grade_value <= 4.0)

    return {
        "exam_id": exam_id,
        "exam_name": exam.name,
        "total_students": len(grades),
        "passing_count": passing_count,
        "failing_count": len(grades) - passing_count,
        "pass_rate": round((passing_count / len(grades)) * 100, 1),
        "points": {
            "min": min(points_list),
            "max": max(points_list),
            "avg": round(sum(points_list) / len(points_list), 2),
        },
        "percentage": {
            "min": min(percentage_list),
            "max": max(percentage_list),
            "avg": round(sum(percentage_list) / len(percentage_list), 2),
        },
        "grades": {
            "min": min(grade_values),
            "max": max(grade_values),
            "avg": round(sum(grade_values) / len(grade_values), 2),
        },
        "distribution": grade_distribution,
    }


def add_exam_component(
    exam_id: int,
    name: str,
    weight: float,
    max_points: float,
    order: int = 0,
    description: str | None = None,
) -> ExamComponent | None:
    """
    Add a component to an exam.

    Args:
        exam_id: Parent exam ID
        name: Component name
        weight: Weight percentage (0-100)
        max_points: Maximum points for component
        order: Display order
        description: Optional description

    Returns:
        Created ExamComponent or None if failed

    Raises:
        ValueError: If validation fails
    """
    exam = db.session.query(Exam).filter_by(id=exam_id).first()
    if not exam:
        raise ValueError(f"Exam with ID {exam_id} not found")

    if weight <= 0 or weight > 100:
        raise ValueError("Weight must be between 0 (exclusive) and 100")

    if max_points <= 0:
        raise ValueError("Max points must be greater than 0")

    # Check total weight doesn't exceed 100%
    existing_weight = db.session.query(
        func.sum(ExamComponent.weight)
    ).filter(ExamComponent.exam_id == exam_id).scalar() or 0

    if existing_weight + weight > 100:
        raise ValueError(
            f"Total component weight would exceed 100% "
            f"(existing: {existing_weight}%, adding: {weight}%)"
        )

    try:
        component = ExamComponent(
            exam_id=exam_id,
            name=name,
            weight=weight,
            max_points=max_points,
            order=order,
            description=description,
        )
        db.session.add(component)
        db.session.commit()

        logger.info(f"Added component '{name}' to exam {exam_id}")
        return component

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while adding component: {e}")
        return None


def list_exam_components(exam_id: int) -> list[ExamComponent]:
    """List all components for an exam."""
    return (
        db.session.query(ExamComponent)
        .filter_by(exam_id=exam_id)
        .order_by(ExamComponent.order)
        .all()
    )


def create_default_grading_scale(university_id: int | None = None) -> GradingScale:
    """
    Create the default German grading scale.

    Args:
        university_id: Optional university to associate with

    Returns:
        Created GradingScale
    """
    scale = GradingScale(
        name="Deutsche Notenskala",
        university_id=university_id,
        is_default=True,
        description="Standard German grading scale (1.0 - 5.0)",
    )
    db.session.add(scale)
    db.session.flush()

    # Add thresholds
    for grade_value, (min_pct, max_pct, description) in GERMAN_GRADES.items():
        threshold = GradeThreshold(
            scale_id=scale.id,
            grade_value=grade_value,
            grade_label=description,
            min_percentage=min_pct,
            description=f"{min_pct}-{max_pct}%",
        )
        db.session.add(threshold)

    db.session.commit()
    logger.info(f"Created default German grading scale (ID: {scale.id})")
    return scale


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Grade Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add grade
    add_parser = subparsers.add_parser("add", help="Add a grade")
    add_parser.add_argument("--enrollment-id", type=int, required=True)
    add_parser.add_argument("--exam-id", type=int, required=True)
    add_parser.add_argument("--points", type=float, required=True)
    add_parser.add_argument("--component-id", type=int, help="For multi-part exams")
    add_parser.add_argument("--graded-by", help="Who is grading")
    add_parser.add_argument("--final", action="store_true", help="Mark as final grade")
    add_parser.add_argument("--notes", help="Grading notes")

    # Update grade
    update_parser = subparsers.add_parser("update", help="Update a grade")
    update_parser.add_argument("grade_id", type=int)
    update_parser.add_argument("--points", type=float)
    update_parser.add_argument("--final", action="store_true")
    update_parser.add_argument("--not-final", action="store_true")
    update_parser.add_argument("--notes")
    update_parser.add_argument("--graded-by")

    # Delete grade
    delete_parser = subparsers.add_parser("delete", help="Delete a grade")
    delete_parser.add_argument("grade_id", type=int)
    delete_parser.add_argument("--yes", action="store_true")

    # List grades
    list_parser = subparsers.add_parser("list", help="List grades")
    list_parser.add_argument("--enrollment-id", type=int)
    list_parser.add_argument("--exam-id", type=int)
    list_parser.add_argument("--course-id", type=int)
    list_parser.add_argument("--final-only", action="store_true")

    # Show grade
    show_parser = subparsers.add_parser("show", help="Show grade details")
    show_parser.add_argument("grade_id", type=int)

    # Calculate average
    avg_parser = subparsers.add_parser("average", help="Calculate weighted average")
    avg_parser.add_argument("--enrollment-id", type=int, required=True)
    avg_parser.add_argument("--course-id", type=int)

    # Exam statistics
    stats_parser = subparsers.add_parser("stats", help="Show exam statistics")
    stats_parser.add_argument("exam_id", type=int)

    # Add component
    comp_parser = subparsers.add_parser("add-component", help="Add exam component")
    comp_parser.add_argument("--exam-id", type=int, required=True)
    comp_parser.add_argument("--name", required=True)
    comp_parser.add_argument("--weight", type=float, required=True, help="Weight %")
    comp_parser.add_argument("--max-points", type=float, required=True)
    comp_parser.add_argument("--order", type=int, default=0)
    comp_parser.add_argument("--description")

    # List components
    list_comp_parser = subparsers.add_parser("list-components", help="List exam components")
    list_comp_parser.add_argument("exam_id", type=int)

    # Create default scale
    scale_parser = subparsers.add_parser("create-scale", help="Create default grading scale")
    scale_parser.add_argument("--university-id", type=int)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    app = create_app()
    with app.app_context():
        try:
            if args.command == "add":
                grade = add_grade(
                    enrollment_id=args.enrollment_id,
                    exam_id=args.exam_id,
                    points=args.points,
                    component_id=args.component_id,
                    graded_by=args.graded_by,
                    is_final=args.final,
                    notes=args.notes,
                )
                if grade:
                    print("\nGrade added successfully!")
                    print(f"ID: {grade.id}")
                    print(f"Points: {grade.points}")
                    print(f"Percentage: {grade.percentage}%")
                    print(f"Grade: {grade.grade_value} ({grade.grade_label})")
                    print(f"Final: {'Yes' if grade.is_final else 'No'}")
                    return 0
                return 1

            if args.command == "update":
                is_final = None
                if args.final:
                    is_final = True
                elif args.not_final:
                    is_final = False

                grade = update_grade(
                    grade_id=args.grade_id,
                    points=args.points,
                    is_final=is_final,
                    notes=args.notes,
                    graded_by=args.graded_by,
                )
                if grade:
                    print("\nGrade updated successfully!")
                    print(f"Points: {grade.points}")
                    print(f"Percentage: {grade.percentage}%")
                    print(f"Grade: {grade.grade_value} ({grade.grade_label})")
                    return 0
                return 1

            if args.command == "delete":
                grade = get_grade(args.grade_id)
                if not grade:
                    print(f"Error: Grade {args.grade_id} not found")
                    return 1

                if not args.yes:
                    print(f"\nDelete grade {args.grade_id}?")
                    print(f"Points: {grade.points}, Grade: {grade.grade_value}")
                    response = input("Type 'yes' to confirm: ")
                    if response.lower() != "yes":
                        print("Cancelled")
                        return 0

                if delete_grade(args.grade_id):
                    print("Grade deleted")
                    return 0
                return 1

            if args.command == "list":
                grades = list_grades(
                    enrollment_id=args.enrollment_id,
                    exam_id=args.exam_id,
                    course_id=args.course_id,
                    is_final=True if args.final_only else None,
                )
                if not grades:
                    print("No grades found")
                    return 0

                print(f"\nFound {len(grades)} grade(s):\n")
                for g in grades:
                    print(f"ID {g.id}: {g.points} pts = {g.percentage}% "
                          f"({g.grade_value} - {g.grade_label})")
                    print(f"  Exam: {g.exam.name}")
                    print(f"  Final: {'Yes' if g.is_final else 'No'}")
                    print()
                return 0

            if args.command == "show":
                grade = get_grade(args.grade_id)
                if not grade:
                    print(f"Error: Grade {args.grade_id} not found")
                    return 1

                print("\nGrade Details:")
                print(f"ID: {grade.id}")
                print(f"Student: {grade.enrollment.student.last_name}, "
                      f"{grade.enrollment.student.first_name}")
                print(f"Exam: {grade.exam.name}")
                if grade.component:
                    print(f"Component: {grade.component.name}")
                print(f"Points: {grade.points}")
                print(f"Percentage: {grade.percentage}%")
                print(f"Grade: {grade.grade_value} ({grade.grade_label})")
                print(f"Final: {'Yes' if grade.is_final else 'No'}")
                print(f"Graded by: {grade.graded_by or 'N/A'}")
                print(f"Graded at: {grade.graded_at}")
                if grade.notes:
                    print(f"Notes: {grade.notes}")
                return 0

            if args.command == "average":
                result = calculate_weighted_average(
                    enrollment_id=args.enrollment_id,
                    course_id=args.course_id,
                )
                if not result:
                    print("No final grades found")
                    return 0

                print(f"\nWeighted Average for {result['student_name']}:")
                print(f"Average Grade: {result['weighted_average']} ({result['grade_label']})")
                print(f"Total Weight: {result['total_weight']}%")
                print(f"Passing: {'Yes' if result['is_passing'] else 'No'}")
                return 0

            if args.command == "stats":
                stats = get_exam_statistics(args.exam_id)
                if not stats:
                    print("No grades found for this exam")
                    return 0

                print(f"\nStatistics for: {stats['exam_name']}")
                print(f"Total Students: {stats['total_students']}")
                print(f"Passing: {stats['passing_count']} ({stats['pass_rate']}%)")
                print(f"Failing: {stats['failing_count']}")
                print(f"\nPoints: min={stats['points']['min']}, "
                      f"max={stats['points']['max']}, avg={stats['points']['avg']}")
                print(f"Grades: min={stats['grades']['min']}, "
                      f"max={stats['grades']['max']}, avg={stats['grades']['avg']}")
                print("\nGrade Distribution:")
                for label, count in sorted(stats['distribution'].items()):
                    print(f"  {label}: {count}")
                return 0

            if args.command == "add-component":
                component = add_exam_component(
                    exam_id=args.exam_id,
                    name=args.name,
                    weight=args.weight,
                    max_points=args.max_points,
                    order=args.order,
                    description=args.description,
                )
                if component:
                    print("\nComponent added!")
                    print(f"ID: {component.id}")
                    print(f"Name: {component.name}")
                    print(f"Weight: {component.weight}%")
                    print(f"Max Points: {component.max_points}")
                    return 0
                return 1

            if args.command == "list-components":
                components = list_exam_components(args.exam_id)
                if not components:
                    print("No components found")
                    return 0

                print(f"\nComponents for exam {args.exam_id}:\n")
                total_weight = 0
                for c in components:
                    print(f"ID {c.id}: {c.name}")
                    print(f"  Weight: {c.weight}%")
                    print(f"  Max Points: {c.max_points}")
                    total_weight += c.weight
                    print()
                print(f"Total Weight: {total_weight}%")
                return 0

            if args.command == "create-scale":
                scale = create_default_grading_scale(args.university_id)
                print(f"\nCreated grading scale: {scale.name} (ID: {scale.id})")
                print("Thresholds:")
                for t in scale.thresholds:
                    print(f"  {t.grade_value} ({t.grade_label}): >= {t.min_percentage}%")
                return 0

        except ValueError as e:
            print(f"Error: {e}")
            return 1
        except IntegrityError as e:
            print(f"Database constraint error: {e}")
            return 1
        except Exception as e:
            logger.exception("Unexpected error")
            print(f"Error: {e}")
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
