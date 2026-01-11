"""
Student service for business logic.

This module provides business logic for student management,
separating concerns from CLI and web interfaces.
"""

import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.student import Student, validate_email, validate_student_id
from app.services.base_service import BaseService

# Configure logging
logger = logging.getLogger(__name__)


class StudentService(BaseService):
    """
    Service class for student-related business logic.

    Handles validation, business rules, and database operations
    for student management.
    """

    def add_student(
        self,
        first_name: str,
        last_name: str,
        student_id: str,
        email: str,
        program: str,
        validate_id: bool = True,
    ) -> Student:
        """
        Add a new student to the database.

        Args:
            first_name: Student's first name
            last_name: Student's last name
            student_id: Student ID (8 digits)
            email: Email address
            program: Study program/major

        Returns:
            Created Student object

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
        if not student_id:
            raise ValueError("Matrikelnummer darf nicht leer sein.")
        if validate_id and not validate_student_id(student_id):
            raise ValueError(
                f"Ungültiges Matrikelnummer-Format: {student_id}. "
                "Die Matrikelnummer muss genau 8 Ziffern haben."
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
            self.add(student)
            self.commit()

            logger.info(f"Successfully created student: {student}")
            return student

        except IntegrityError as e:
            self.rollback()
            if "student_id" in str(e):
                raise ValueError(
                    f"Student mit Matrikelnummer '{student_id}' existiert bereits"
                ) from e
            if "email" in str(e):
                raise ValueError(
                    f"Student mit E-Mail-Adresse '{email}' existiert bereits"
                ) from e
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while adding student: {e}")
            raise

    def list_students(
        self, search: str | None = None, program: str | None = None
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
            query = self.query(Student).filter(Student.deleted_at.is_(None))

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

    def get_student(self, student_id: int) -> Student | None:
        """
        Get a student by database ID.

        Args:
            student_id: Student database ID

        Returns:
            Student object or None if not found
        """
        try:
            student = (
                self.query(Student)
                .filter_by(id=student_id)
                .filter(Student.deleted_at.is_(None))
                .first()
            )

            if student:
                logger.info(f"Found student: {student}")
            else:
                logger.warning(f"Student with ID {student_id} not found")

            return student

        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching student: {e}")
            raise

    def get_student_by_student_id(self, student_id: str) -> Student | None:
        """
        Get a student by their student ID number.

        Args:
            student_id: Student ID number (8 digits)

        Returns:
            Student object or None if not found
        """
        try:
            student = (
                self.query(Student)
                .filter_by(student_id=student_id)
                .filter(Student.deleted_at.is_(None))
                .first()
            )

            if student:
                logger.info(f"Found student: {student}")
            else:
                logger.warning(f"Student with student_id {student_id} not found")

            return student

        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching student: {e}")
            raise

    def update_student(
        self,
        student_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        student_number: str | None = None,
        email: str | None = None,
        program: str | None = None,
        validate_id: bool = True,
    ) -> Student | None:
        """
        Update a student's information.

        Args:
            student_id: Student database ID
            first_name: New first name (optional)
            last_name: New last name (optional)
            student_number: New student ID (optional)
            email: New email (optional)
            program: New program (optional)

        Returns:
            Updated Student object or None if not found

        Raises:
            ValueError: If validation fails
            IntegrityError: If updated values conflict with existing records
        """
        if all(
            v is None for v in [first_name, last_name, student_number, email, program]
        ):
            raise ValueError("At least one field must be provided for update")

        try:
            student = (
                self.query(Student)
                .filter_by(id=student_id)
                .filter(Student.deleted_at.is_(None))
                .first()
            )

            if not student:
                logger.warning(f"Student with ID {student_id} not found")
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

            if student_number is not None:
                student_number = student_number.strip()
                if not student_number:
                    raise ValueError("Matrikelnummer darf nicht leer sein.")
                if validate_id and not validate_student_id(student_number):
                    raise ValueError(
                        f"Ungültiges Matrikelnummer-Format: {student_number}. "
                        "Die Matrikelnummer muss genau 8 Ziffern haben."
                    )
                student.student_id = student_number

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

            self.commit()
            logger.info(f"Successfully updated student: {student}")
            return student

        except IntegrityError as e:
            self.rollback()
            if "student_id" in str(e):
                raise ValueError(
                    f"Student mit Matrikelnummer '{student_number}' existiert bereits"
                ) from e
            if "email" in str(e):
                raise ValueError(
                    f"Student mit E-Mail-Adresse '{email}' existiert bereits"
                ) from e
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while updating student: {e}")
            raise

    def delete_student(self, student_id: int) -> bool:
        """
        Delete a student by ID.

        Args:
            student_id: Student database ID

        Returns:
            True if deleted, False if not found
        """
        try:
            student = (
                self.query(Student)
                .filter_by(id=student_id)
                .filter(Student.deleted_at.is_(None))
                .first()
            )

            if not student:
                logger.warning(f"Student with ID {student_id} not found")
                return False

            student.soft_delete()
            self.commit()
            logger.info(f"Successfully deleted student: {student}")
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while deleting student: {e}")
            raise
