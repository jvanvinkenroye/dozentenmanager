"""
Student management CLI tool.

This module provides command-line interface for managing student records,
including adding, updating, listing, and deleting students.
"""

import argparse
import logging
import sys
from typing import Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db
from app import create_app
from app.models.student import Student, validate_email, validate_student_id

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def add_student(
    first_name: str,
    last_name: str,
    student_id: str,
    email: str,
    program: str,
) -> Optional[Student]:
    """
    Add a new student to the database.

    Args:
        first_name: Student's first name
        last_name: Student's last name
        student_id: Student ID (8 digits)
        email: Email address
        program: Study program/major

    Returns:
        Created Student object or None if failed

    Raises:
        ValueError: If validation fails
        IntegrityError: If student with same student_id or email already exists
    """
    # Validate first name
    if not first_name or not first_name.strip():
        raise ValueError("First name cannot be empty")

    first_name = first_name.strip()
    if len(first_name) > 100:
        raise ValueError("First name cannot exceed 100 characters")

    # Validate last name
    if not last_name or not last_name.strip():
        raise ValueError("Last name cannot be empty")

    last_name = last_name.strip()
    if len(last_name) > 100:
        raise ValueError("Last name cannot exceed 100 characters")

    # Validate student ID
    student_id = student_id.strip()
    if not validate_student_id(student_id):
        raise ValueError(
            f"Invalid student ID format: {student_id}. "
            "Student ID must be exactly 8 digits."
        )

    # Validate email
    email = email.strip().lower()
    if not validate_email(email):
        raise ValueError(f"Invalid email format: {email}")

    if len(email) > 255:
        raise ValueError("Email cannot exceed 255 characters")

    # Validate program
    if not program or not program.strip():
        raise ValueError("Program cannot be empty")

    program = program.strip()
    if len(program) > 200:
        raise ValueError("Program cannot exceed 200 characters")

    try:
        # Create new student
        student = Student(
            first_name=first_name,
            last_name=last_name,
            student_id=student_id,
            email=email,
            program=program,
        )
        db.session.add(student)
        db.session.commit()

        logger.info(f"Successfully created student: {student}")
        return student

    except IntegrityError as e:
        db.session.rollback()
        if "student_id" in str(e):
            raise ValueError(f"Student with ID '{student_id}' already exists") from e
        elif "email" in str(e):
            raise ValueError(f"Student with email '{email}' already exists") from e
        else:
            raise

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while adding student: {e}")
        raise


def list_students(
    search: Optional[str] = None, program: Optional[str] = None
) -> list[Student]:
    """
    List all students, optionally filtered by search term or program.

    Args:
        search: Optional search term to filter by name, student_id, or email
        program: Optional program filter

    Returns:
        List of Student objects
    """
    try:
        query = db.session.query(Student)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Student.first_name.ilike(search_term))
                | (Student.last_name.ilike(search_term))
                | (Student.student_id.ilike(search_term))
                | (Student.email.ilike(search_term))
            )

        if program:
            program_term = f"%{program}%"
            query = query.filter(Student.program.ilike(program_term))

        students = query.order_by(Student.last_name, Student.first_name).all()
        logger.info(f"Found {len(students)} students")
        return students

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing students: {e}")
        raise


def get_student(student_db_id: int) -> Optional[Student]:
    """
    Get a student by database ID.

    Args:
        student_db_id: Database ID

    Returns:
        Student object or None if not found
    """
    try:
        student = db.session.query(Student).filter_by(id=student_db_id).first()

        if student:
            logger.info(f"Found student: {student}")
        else:
            logger.warning(f"Student with ID {student_db_id} not found")

        return student

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching student: {e}")
        raise


def get_student_by_student_id(student_id: str) -> Optional[Student]:
    """
    Get a student by student ID.

    Args:
        student_id: Student ID (8 digits)

    Returns:
        Student object or None if not found
    """
    try:
        student = db.session.query(Student).filter_by(student_id=student_id).first()

        if student:
            logger.info(f"Found student: {student}")
        else:
            logger.warning(f"Student with student ID {student_id} not found")

        return student

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching student: {e}")
        raise


def update_student(
    student_db_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    student_id: Optional[str] = None,
    email: Optional[str] = None,
    program: Optional[str] = None,
) -> Optional[Student]:
    """
    Update a student's information.

    Args:
        student_db_id: Database ID
        first_name: New first name (optional)
        last_name: New last name (optional)
        student_id: New student ID (optional)
        email: New email (optional)
        program: New program (optional)

    Returns:
        Updated Student object or None if not found

    Raises:
        ValueError: If validation fails
        IntegrityError: If updated values conflict with existing records
    """
    if all(v is None for v in [first_name, last_name, student_id, email, program]):
        raise ValueError("At least one field must be provided for update")

    try:
        student = db.session.query(Student).filter_by(id=student_db_id).first()

        if not student:
            logger.warning(f"Student with ID {student_db_id} not found")
            return None

        # Update fields if provided
        if first_name is not None:
            first_name = first_name.strip()
            if not first_name:
                raise ValueError("First name cannot be empty")
            if len(first_name) > 100:
                raise ValueError("First name cannot exceed 100 characters")
            student.first_name = first_name

        if last_name is not None:
            last_name = last_name.strip()
            if not last_name:
                raise ValueError("Last name cannot be empty")
            if len(last_name) > 100:
                raise ValueError("Last name cannot exceed 100 characters")
            student.last_name = last_name

        if student_id is not None:
            student_id = student_id.strip()
            if not validate_student_id(student_id):
                raise ValueError(
                    f"Invalid student ID format: {student_id}. "
                    "Student ID must be exactly 8 digits."
                )
            student.student_id = student_id

        if email is not None:
            email = email.strip().lower()
            if not validate_email(email):
                raise ValueError(f"Invalid email format: {email}")
            if len(email) > 255:
                raise ValueError("Email cannot exceed 255 characters")
            student.email = email

        if program is not None:
            program = program.strip()
            if not program:
                raise ValueError("Program cannot be empty")
            if len(program) > 200:
                raise ValueError("Program cannot exceed 200 characters")
            student.program = program

        db.session.commit()
        logger.info(f"Successfully updated student: {student}")
        return student

    except IntegrityError as e:
        db.session.rollback()
        if "student_id" in str(e):
            raise ValueError(f"Student with ID '{student_id}' already exists") from e
        elif "email" in str(e):
            raise ValueError(f"Student with email '{email}' already exists") from e
        else:
            raise

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while updating student: {e}")
        raise


def delete_student(student_db_id: int) -> bool:
    """
    Delete a student by database ID.

    Args:
        student_db_id: Database ID

    Returns:
        True if deleted, False if not found
    """
    try:
        student = db.session.query(Student).filter_by(id=student_db_id).first()

        if not student:
            logger.warning(f"Student with ID {student_db_id} not found")
            return False

        db.session.delete(student)
        db.session.commit()
        logger.info(f"Successfully deleted student: {student}")
        return True

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while deleting student: {e}")
        raise


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
        try:
            if args.command == "add":
                student = add_student(
                    args.first_name,
                    args.last_name,
                    args.student_id,
                    args.email,
                    args.program,
                )
                if student:
                    print(
                        f"Created student: ID={student.id}, "
                        f"Name={student.first_name} {student.last_name}, "
                        f"Student ID={student.student_id}, "
                        f"Email={student.email}"
                    )
                return 0

            elif args.command == "list":
                students = list_students(args.search, args.program)
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

            elif args.command == "show":
                student = get_student(args.id)
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

            elif args.command == "update":
                student = update_student(
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
                else:
                    print(f"Student with ID {args.id} not found")
                    return 1

            elif args.command == "delete":
                if delete_student(args.id):
                    print(f"Student with ID {args.id} deleted successfully")
                    return 0
                else:
                    print(f"Student with ID {args.id} not found")
                    return 1

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
