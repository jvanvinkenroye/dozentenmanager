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
from datetime import date

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db
from app.models.course import Course
from app.models.enrollment import VALID_STATUSES, Enrollment, validate_status
from app.models.student import Student

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def add_enrollment(student_id_str: str, course_id: int) -> int:
    """
    Enroll a student in a course.

    Args:
        student_id_str: Student ID (matriculation number)
        course_id: Course database ID

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Verify student exists
        student = db.session.query(Student).filter_by(student_id=student_id_str).first()
        if not student:
            logger.error(f"Student with ID {student_id_str} not found")
            return 1

        # Verify course exists
        course = db.session.query(Course).filter_by(id=course_id).first()
        if not course:
            logger.error(f"Course with ID {course_id} not found")
            return 1

        # Create enrollment
        enrollment = Enrollment(
            student_id=student.id,
            course_id=course.id,
            status="active",
        )

        db.session.add(enrollment)
        db.session.commit()

        logger.info(
            f"Successfully enrolled {student.first_name} {student.last_name} "
            f"(ID: {student.student_id}) in '{course.name}' (Semester: {course.semester})"
        )
        return 0

    except IntegrityError:
        db.session.rollback()
        logger.error(
            f"Student {student_id_str} is already enrolled in course {course_id}"
        )
        return 1
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error: {e}")
        return 1


def list_enrollments(
    course_id: int | None = None,
    student_id_str: str | None = None,
) -> int:
    """
    List enrollments by course or student.

    Args:
        course_id: Course ID to filter by (optional)
        student_id_str: Student ID to filter by (optional)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        query = db.session.query(Enrollment)

        if course_id:
            query = query.filter_by(course_id=course_id)
        elif student_id_str:
            # Get student database ID from student_id
            student = (
                db.session.query(Student).filter_by(student_id=student_id_str).first()
            )
            if not student:
                logger.error(f"Student with ID {student_id_str} not found")
                return 1
            query = query.filter_by(student_id=student.id)

        enrollments = query.all()

        if not enrollments:
            logger.info("No enrollments found")
            return 0

        logger.info(f"Found {len(enrollments)} enrollment(s):")
        print("\n" + "=" * 100)
        print(
            f"{'Student ID':<12} {'Student Name':<25} {'Course':<30} {'Semester':<12} {'Status':<10}"
        )
        print("=" * 100)

        for enrollment in enrollments:
            student_name = (
                f"{enrollment.student.first_name} {enrollment.student.last_name}"
            )
            print(
                f"{enrollment.student.student_id:<12} "
                f"{student_name:<25} "
                f"{enrollment.course.name:<30} "
                f"{enrollment.course.semester:<12} "
                f"{enrollment.status:<10}"
            )

        print("=" * 100 + "\n")
        return 0

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return 1


def remove_enrollment(student_id_str: str, course_id: int) -> int:
    """
    Remove a student's enrollment from a course.

    Args:
        student_id_str: Student ID (matriculation number)
        course_id: Course database ID

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Get student database ID
        student = db.session.query(Student).filter_by(student_id=student_id_str).first()
        if not student:
            logger.error(f"Student with ID {student_id_str} not found")
            return 1

        # Find enrollment
        enrollment = (
            db.session.query(Enrollment)
            .filter_by(student_id=student.id, course_id=course_id)
            .first()
        )

        if not enrollment:
            logger.error(
                f"No enrollment found for student {student_id_str} in course {course_id}"
            )
            return 1

        # Get course name before deleting enrollment
        course_name = enrollment.course.name
        student_first_name = student.first_name
        student_last_name = student.last_name

        db.session.delete(enrollment)
        db.session.commit()

        logger.info(
            f"Successfully removed enrollment for {student_first_name} {student_last_name} "
            f"from course {course_name}"
        )
        return 0

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error: {e}")
        return 1


def update_enrollment_status(student_id_str: str, course_id: int, status: str) -> int:
    """
    Update enrollment status.

    Args:
        student_id_str: Student ID (matriculation number)
        course_id: Course database ID
        status: New status (active, completed, dropped)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Validate status
        if not validate_status(status):
            logger.error(
                f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}"
            )
            return 1

        # Get student database ID
        student = db.session.query(Student).filter_by(student_id=student_id_str).first()
        if not student:
            logger.error(f"Student with ID {student_id_str} not found")
            return 1

        # Find enrollment
        enrollment = (
            db.session.query(Enrollment)
            .filter_by(student_id=student.id, course_id=course_id)
            .first()
        )

        if not enrollment:
            logger.error(
                f"No enrollment found for student {student_id_str} in course {course_id}"
            )
            return 1

        old_status = enrollment.status
        enrollment.status = status

        # Set unenrollment date when status changes to dropped
        if status == "dropped" and not enrollment.unenrollment_date:
            enrollment.unenrollment_date = date.today()

        db.session.commit()

        logger.info(
            f"Updated enrollment status from '{old_status}' to '{status}' for "
            f"{student.first_name} {student.last_name} in course {enrollment.course.name}"
        )
        return 0

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error: {e}")
        return 1


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

    # Initialize Flask app to get database session
    from app import create_app

    app = create_app()

    with app.app_context():
        if args.command == "add":
            return add_enrollment(args.student_id, args.course_id)
        if args.command == "list":
            return list_enrollments(
                course_id=args.course_id,
                student_id_str=args.student_id,
            )
        if args.command == "remove":
            return remove_enrollment(args.student_id, args.course_id)
        if args.command == "status":
            return update_enrollment_status(
                args.student_id, args.course_id, args.status
            )

    return 1


if __name__ == "__main__":
    sys.exit(main())
