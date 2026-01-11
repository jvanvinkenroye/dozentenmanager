"""
Grade management CLI tool.

This module provides command-line interface for managing grades,
including adding grades, calculating weighted averages, and
managing grading scales.
"""

import argparse
import logging
import sys

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import create_app
from app.services.grade_service import GradeService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
    list_comp_parser = subparsers.add_parser(
        "list-components", help="List exam components"
    )
    list_comp_parser.add_argument("exam_id", type=int)

    # Create default scale
    scale_parser = subparsers.add_parser(
        "create-scale", help="Create default grading scale"
    )
    scale_parser.add_argument("--university-id", type=int)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    app = create_app()
    with app.app_context():
        service = GradeService()

        try:
            if args.command == "add":
                grade = service.add_grade(
                    enrollment_id=args.enrollment_id,
                    exam_id=args.exam_id,
                    points=args.points,
                    component_id=args.component_id,
                    graded_by=args.graded_by,
                    is_final=args.final,
                    notes=args.notes,
                )
                print("\nGrade added successfully!")
                print(f"ID: {grade.id}")
                print(f"Points: {grade.points}")
                print(f"Percentage: {grade.percentage}%")
                print(f"Grade: {grade.grade_value} ({grade.grade_label})")
                print(f"Final: {'Yes' if grade.is_final else 'No'}")
                return 0

            if args.command == "update":
                is_final = None
                if args.final:
                    is_final = True
                elif args.not_final:
                    is_final = False

                grade = service.update_grade(
                    grade_id=args.grade_id,
                    points=args.points,
                    is_final=is_final,
                    notes=args.notes,
                    graded_by=args.graded_by,
                )
                print("\nGrade updated successfully!")
                print(f"ID: {grade.id}")
                print(f"Points: {grade.points}")
                print(f"Percentage: {grade.percentage}%")
                print(f"Grade: {grade.grade_value} ({grade.grade_label})")
                print(f"Final: {'Yes' if grade.is_final else 'No'}")
                return 0

            if args.command == "delete":
                grade = service.get_grade(args.grade_id)

                if not args.yes:
                    print("\nAre you sure you want to delete this grade?")
                    print(f"ID: {grade.id}")
                    print(f"Points: {grade.points}")
                    print(f"Grade: {grade.grade_value} ({grade.grade_label})")
                    response = input("\nType 'yes' to confirm: ")
                    if response.lower() != "yes":
                        print("Deletion cancelled")
                        return 0

                service.delete_grade(args.grade_id)
                print("Grade deleted successfully")
                return 0

            if args.command == "show":
                grade = service.get_grade(args.grade_id)
                print("\nGrade Details:")
                print(f"ID: {grade.id}")
                print(f"Enrollment ID: {grade.enrollment_id}")
                print(f"Exam ID: {grade.exam_id}")
                if grade.component_id:
                    print(f"Component ID: {grade.component_id}")
                print(f"Points: {grade.points}")
                print(f"Percentage: {grade.percentage}%")
                print(f"Grade: {grade.grade_value} ({grade.grade_label})")
                print(f"Final: {'Yes' if grade.is_final else 'No'}")
                if grade.graded_by:
                    print(f"Graded by: {grade.graded_by}")
                if grade.notes:
                    print(f"Notes: {grade.notes}")
                print(f"Graded at: {grade.graded_at}")
                return 0

            if args.command == "list":
                grades = service.list_grades(
                    enrollment_id=args.enrollment_id,
                    exam_id=args.exam_id,
                    course_id=args.course_id,
                    is_final=True if args.final_only else None,
                )

                if not grades:
                    print("No grades found")
                    return 0

                print(f"\nFound {len(grades)} grade(s):\n")
                for grade in grades:
                    print(f"ID {grade.id}:")
                    print(
                        f"  Student: {grade.enrollment.student.last_name}, {grade.enrollment.student.first_name}"
                    )
                    print(f"  Exam: {grade.exam.name}")
                    if grade.component_id:
                        print(f"  Component: {grade.component.name}")
                    print(f"  Points: {grade.points} ({grade.percentage}%)")
                    print(f"  Grade: {grade.grade_value} ({grade.grade_label})")
                    print(f"  Final: {'Yes' if grade.is_final else 'No'}")
                    print()
                return 0

            if args.command == "average":
                result = service.calculate_weighted_average(
                    enrollment_id=args.enrollment_id,
                    course_id=args.course_id,
                )

                if not result:
                    print("No final grades found for this enrollment")
                    return 1

                print("\nWeighted Average Calculation:")
                print(f"Student: {result['student_name']}")
                print(
                    f"Weighted Average: {result['weighted_average']} ({result['grade_label']})"
                )
                print(f"Total Weight: {result['total_weight']}%")
                print(f"Passing: {'Yes' if result['is_passing'] else 'No'}")
                print("\nPer-Exam Breakdown:")
                for _exam_id, exam_data in result["exam_grades"].items():
                    print(
                        f"\n  {exam_data['exam_name']} (Weight: {exam_data['exam_weight']}%)"
                    )
                    if exam_data["components"]:
                        print("    Components:")
                        for comp in exam_data["components"]:
                            print(
                                f"      - {comp['component_name']}: {comp['points']} pts ({comp['percentage']}%) = {comp['grade']}"
                            )
                    if exam_data["final_grade"]:
                        fg = exam_data["final_grade"]
                        print(
                            f"    Final: {fg['points']} pts ({fg['percentage']}%) = {fg['grade']}"
                        )
                return 0

            if args.command == "stats":
                stats = service.get_exam_statistics(args.exam_id)

                if not stats:
                    print("No grades found for this exam")
                    return 1

                print(f"\nExam Statistics: {stats['exam_name']}")
                print(f"Total Students: {stats['total_students']}")
                print(f"Passing: {stats['passing_count']} ({stats['pass_rate']}%)")
                print(f"Failing: {stats['failing_count']}")
                print("\nPoints:")
                print(f"  Min: {stats['points']['min']}")
                print(f"  Max: {stats['points']['max']}")
                print(f"  Avg: {stats['points']['avg']}")
                print("\nPercentages:")
                print(f"  Min: {stats['percentage']['min']}%")
                print(f"  Max: {stats['percentage']['max']}%")
                print(f"  Avg: {stats['percentage']['avg']}%")
                print("\nGrades:")
                print(f"  Best: {stats['grades']['min']}")
                print(f"  Worst: {stats['grades']['max']}")
                print(f"  Avg: {stats['grades']['avg']}")
                print("\nGrade Distribution:")
                for label, count in sorted(stats["distribution"].items()):
                    print(f"  {label}: {count}")
                return 0

            if args.command == "add-component":
                component = service.add_exam_component(
                    exam_id=args.exam_id,
                    name=args.name,
                    weight=args.weight,
                    max_points=args.max_points,
                    order=args.order,
                    description=args.description,
                )
                print("\nExam component added successfully!")
                print(f"ID: {component.id}")
                print(f"Name: {component.name}")
                print(f"Weight: {component.weight}%")
                print(f"Max Points: {component.max_points}")
                print(f"Order: {component.order}")
                return 0

            if args.command == "list-components":
                components = service.list_exam_components(args.exam_id)

                if not components:
                    print("No components found for this exam")
                    return 0

                print(f"\nFound {len(components)} component(s):\n")
                for comp in components:
                    print(f"ID {comp.id}: {comp.name}")
                    print(f"  Weight: {comp.weight}%")
                    print(f"  Max Points: {comp.max_points}")
                    print(f"  Order: {comp.order}")
                    if comp.description:
                        print(f"  Description: {comp.description}")
                    print()
                return 0

            if args.command == "create-scale":
                scale = service.create_default_grading_scale(
                    university_id=args.university_id
                )
                print("\nGrading scale created successfully!")
                print(f"ID: {scale.id}")
                print(f"Name: {scale.name}")
                print(f"Description: {scale.description}")
                print(f"Default: {'Yes' if scale.is_default else 'No'}")
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
