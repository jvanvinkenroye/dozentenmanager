"""
Enrollment service for business logic.

This module provides business logic for enrollment management,
separating concerns from CLI and web interfaces.
"""

import logging
from datetime import date

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.course import Course
from app.models.enrollment import VALID_STATUSES, Enrollment, validate_status
from app.models.student import Student
from app.services.audit_service import AuditService
from app.services.base_service import BaseService

# Configure logging
logger = logging.getLogger(__name__)


class EnrollmentService(BaseService):
    """
    Service class for enrollment-related business logic.

    Handles validation, business rules, and database operations
    for enrollment management.
    """

    def add_enrollment(self, student_id_str: str, course_id: int) -> Enrollment:
        """
        Enroll a student in a course.

        Args:
            student_id_str: Student ID (matriculation number)
            course_id: Course database ID

        Returns:
            Created Enrollment object

        Raises:
            ValueError: If student or course not found
            IntegrityError: If student already enrolled in course
        """
        try:
            # Verify student exists
            student = (
                self.query(Student)
                .filter_by(student_id=student_id_str)
                .filter(Student.deleted_at.is_(None))
                .first()
            )
            if not student:
                raise ValueError(
                    f"Student mit Matrikelnummer {student_id_str} nicht gefunden"
                )

            # Verify course exists
            course = self.query(Course).filter_by(id=course_id).first()
            if not course:
                raise ValueError(f"Course with ID {course_id} not found")

            # Create enrollment
            enrollment = Enrollment(
                student_id=student.id,
                course_id=course.id,
                status="active",
            )

            self.add(enrollment)
            self.commit()

            # Log enrollment
            AuditService.log(
                action="enroll",
                target_type="Enrollment",
                target_id=enrollment.id,
                details={
                    "student_id": student.id,
                    "student_number": student.student_id,
                    "course_id": course.id,
                    "course_name": course.name,
                },
            )

            logger.info(
                f"Successfully enrolled {student.first_name} {student.last_name} "
                f"(ID: {student.student_id}) in '{course.name}' (Semester: {course.semester})"
            )
            return enrollment

        except IntegrityError as e:
            self.rollback()
            logger.error(
                f"Student {student_id_str} is already enrolled in course {course_id}"
            )
            raise IntegrityError(
                f"Student {student_id_str} is already enrolled in this course",
                params=None,
                orig=e.orig,  # type: ignore[arg-type]
            ) from e

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while adding enrollment: {e}")
            raise

    def list_enrollments(
        self,
        course_id: int | None = None,
        student_id_str: str | None = None,
    ) -> list[Enrollment]:
        """
        List enrollments by course or student.

        Args:
            course_id: Course ID to filter by (optional)
            student_id_str: Student ID to filter by (optional)

        Returns:
            List of Enrollment objects matching the filters

        Raises:
            ValueError: If student_id_str provided but student not found
        """
        try:
            query = self.query(Enrollment)

            if course_id:
                query = query.filter_by(course_id=course_id)
            elif student_id_str:
                # Get student database ID from student_id
                student = (
                    self.query(Student)
                    .filter_by(student_id=student_id_str)
                    .filter(Student.deleted_at.is_(None))
                    .first()
                )
                if not student:
                    raise ValueError(
                        f"Student mit Matrikelnummer {student_id_str} nicht gefunden"
                    )
                query = query.filter_by(student_id=student.id)

            return query.all()

        except SQLAlchemyError as e:
            logger.error(f"Database error while listing enrollments: {e}")
            raise

    def get_enrollment(self, student_id_str: str, course_id: int) -> Enrollment | None:
        """
        Get a specific enrollment.

        Args:
            student_id_str: Student ID (matriculation number)
            course_id: Course database ID

        Returns:
            Enrollment object or None if not found

        Raises:
            ValueError: If student not found
        """
        try:
            # Get student database ID
            student = (
                self.query(Student)
                .filter_by(student_id=student_id_str)
                .filter(Student.deleted_at.is_(None))
                .first()
            )
            if not student:
                raise ValueError(
                    f"Student mit Matrikelnummer {student_id_str} nicht gefunden"
                )

            # Find enrollment
            return (
                self.query(Enrollment)
                .filter_by(student_id=student.id, course_id=course_id)
                .first()
            )

        except SQLAlchemyError as e:
            logger.error(f"Database error while getting enrollment: {e}")
            raise

    def remove_enrollment(self, student_id_str: str, course_id: int) -> bool:
        """
        Remove a student's enrollment from a course.

        Args:
            student_id_str: Student ID (matriculation number)
            course_id: Course database ID

        Returns:
            True if enrollment was removed

        Raises:
            ValueError: If student not found or enrollment not found
        """
        try:
            # Get student database ID
            student = (
                self.query(Student)
                .filter_by(student_id=student_id_str)
                .filter(Student.deleted_at.is_(None))
                .first()
            )
            if not student:
                raise ValueError(
                    f"Student mit Matrikelnummer {student_id_str} nicht gefunden"
                )

            # Find enrollment
            enrollment = (
                self.query(Enrollment)
                .filter_by(student_id=student.id, course_id=course_id)
                .first()
            )

            if not enrollment:
                raise ValueError(
                    f"No enrollment found for student {student_id_str} in course {course_id}"
                )

            # Get information before deleting
            course_name = enrollment.course.name
            student_name = f"{student.first_name} {student.last_name}"
            enrollment_id = enrollment.id
            course_id_val = enrollment.course_id
            student_db_id = student.id

            self.delete(enrollment)
            self.commit()

            # Log unenrollment
            AuditService.log(
                action="unenroll",
                target_type="Enrollment",
                target_id=enrollment_id,
                details={
                    "student_id": student_db_id,
                    "student_number": student_id_str,
                    "course_id": course_id_val,
                    "course_name": course_name,
                },
            )

            logger.info(
                f"Successfully removed enrollment for {student_name} from course {course_name}"
            )
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while removing enrollment: {e}")
            raise

    def update_enrollment_status(
        self, student_id_str: str, course_id: int, status: str
    ) -> Enrollment:
        """
        Update enrollment status.

        Args:
            student_id_str: Student ID (matriculation number)
            course_id: Course database ID
            status: New status (active, completed, dropped)

        Returns:
            Updated Enrollment object

        Raises:
            ValueError: If validation fails or enrollment not found
        """
        # Validate status
        if not validate_status(status):
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}"
            )

        try:
            # Get student database ID
            student = (
                self.query(Student)
                .filter_by(student_id=student_id_str)
                .filter(Student.deleted_at.is_(None))
                .first()
            )
            if not student:
                raise ValueError(
                    f"Student mit Matrikelnummer {student_id_str} nicht gefunden"
                )

            # Find enrollment
            enrollment = (
                self.query(Enrollment)
                .filter_by(student_id=student.id, course_id=course_id)
                .first()
            )

            if not enrollment:
                raise ValueError(
                    f"No enrollment found for student {student_id_str} in course {course_id}"
                )

            old_status = enrollment.status
            enrollment.status = status

            # Set unenrollment date when status changes to dropped
            if status == "dropped" and not enrollment.unenrollment_date:
                enrollment.unenrollment_date = date.today()

            self.commit()

            # Log status update
            AuditService.log(
                action="update_status",
                target_type="Enrollment",
                target_id=enrollment.id,
                details={
                    "student_number": student_id_str,
                    "course_id": course_id,
                    "old_status": old_status,
                    "new_status": status,
                },
            )

            logger.info(
                f"Updated enrollment status from '{old_status}' to '{status}' for "
                f"{student.first_name} {student.last_name} in course {enrollment.course.name}"
            )
            return enrollment

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while updating enrollment status: {e}")
            raise
