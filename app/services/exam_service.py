"""
Exam service for business logic.

This module provides business logic for exam management,
separating concerns from CLI and web interfaces.
"""

import logging
from datetime import date

from sqlalchemy.exc import SQLAlchemyError

from app.models.course import Course
from app.models.exam import (
    Exam,
    validate_exam_date,
    validate_max_points,
    validate_weight,
)
from app.services.audit_service import AuditService
from app.services.base_service import BaseService

# Configure logging
logger = logging.getLogger(__name__)


class ExamService(BaseService):
    """
    Service class for exam-related business logic.

    Handles validation, business rules, and database operations
    for exam management.
    """

    def add_exam(
        self,
        name: str,
        course_id: int,
        exam_date: date,
        max_points: float,
        weight: float = 100.0,
        description: str | None = None,
    ) -> Exam:
        """
        Add a new exam to the database.

        Args:
            name: Exam name (e.g., "Klausur Statistik I")
            course_id: Course ID (foreign key)
            exam_date: Date of the exam
            max_points: Maximum achievable points
            weight: Percentage weight for final grade (0-100, default 100)
            description: Optional description/notes

        Returns:
            Created Exam object

        Raises:
            ValueError: If validation fails
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Exam name cannot be empty")

        name = name.strip()
        if len(name) > 255:
            raise ValueError("Exam name cannot exceed 255 characters")

        # Validate course exists
        try:
            course = self.query(Course).filter_by(id=course_id).first()
            if not course:
                raise ValueError(f"Course with ID {course_id} not found")
        except SQLAlchemyError as e:
            logger.error(f"Database error while checking course: {e}")
            raise ValueError(f"Error checking course: {e}") from e

        # Validate exam date
        if not validate_exam_date(exam_date):
            raise ValueError("Invalid exam date")

        # Validate max points
        if not validate_max_points(max_points):
            raise ValueError("Maximum points must be greater than 0")

        # Validate weight
        if not validate_weight(weight):
            raise ValueError("Weight must be between 0 and 100")

        # Validate description length
        if description:
            description = description.strip()
            if len(description) > 500:
                raise ValueError("Description cannot exceed 500 characters")

        try:
            # Create new exam
            exam = Exam(
                name=name,
                course_id=course_id,
                exam_date=exam_date,
                max_points=max_points,
                weight=weight,
                description=description,
            )
            self.add(exam)
            self.commit()

            # Log creation
            AuditService.log(
                action="create",
                target_type="Exam",
                target_id=exam.id,
                details={
                    "name": exam.name,
                    "course_id": exam.course_id,
                    "exam_date": str(exam.exam_date),
                    "max_points": exam.max_points,
                    "weight": exam.weight,
                },
            )

            logger.info(
                f"Successfully added exam: {exam.name} for course {course.name} "
                f"on {exam_date}"
            )
            return exam

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while adding exam: {e}")
            raise

    def list_exams(self, course_id: int | None = None) -> list[Exam]:
        """
        List all exams with optional course filter.

        Args:
            course_id: Optional course ID filter

        Returns:
            List of Exam objects matching the filter
        """
        try:
            query = self.query(Exam)

            if course_id:
                query = query.filter_by(course_id=course_id)

            return query.order_by(Exam.exam_date.desc(), Exam.name).all()

        except SQLAlchemyError as e:
            logger.error(f"Database error while listing exams: {e}")
            raise

    def get_exam(self, exam_id: int) -> Exam | None:
        """
        Get an exam by ID.

        Args:
            exam_id: Exam database ID

        Returns:
            Exam object or None if not found
        """
        try:
            return self.query(Exam).filter_by(id=exam_id).first()

        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching exam: {e}")
            raise

    def update_exam(
        self,
        exam_id: int,
        name: str | None = None,
        course_id: int | None = None,
        exam_date: date | None = None,
        max_points: float | None = None,
        weight: float | None = None,
        description: str | None = None,
    ) -> Exam:
        """
        Update an existing exam.

        Args:
            exam_id: Exam database ID
            name: Optional new name
            course_id: Optional new course ID
            exam_date: Optional new exam date
            max_points: Optional new max points
            weight: Optional new weight
            description: Optional new description

        Returns:
            Updated Exam object

        Raises:
            ValueError: If validation fails or exam not found
        """
        try:
            exam = self.query(Exam).filter_by(id=exam_id).first()

            if not exam:
                raise ValueError(f"Exam with ID {exam_id} not found")

            # Track changes
            changes = {}

            # Update name
            if name is not None:
                name = name.strip()
                if not name:
                    raise ValueError("Exam name cannot be empty")
                if len(name) > 255:
                    raise ValueError("Exam name cannot exceed 255 characters")
                if exam.name != name:
                    changes["name"] = {"old": exam.name, "new": name}
                    exam.name = name

            # Update course
            if course_id is not None:
                course = self.query(Course).filter_by(id=course_id).first()
                if not course:
                    raise ValueError(f"Course with ID {course_id} not found")
                if exam.course_id != course_id:
                    changes["course_id"] = {"old": exam.course_id, "new": course_id}
                    exam.course_id = course_id

            # Update exam date
            if exam_date is not None:
                if not validate_exam_date(exam_date):
                    raise ValueError("Invalid exam date")
                if exam.exam_date != exam_date:
                    changes["exam_date"] = {"old": str(exam.exam_date), "new": str(exam_date)}
                    exam.exam_date = exam_date

            # Update max points
            if max_points is not None:
                if not validate_max_points(max_points):
                    raise ValueError("Maximum points must be greater than 0")
                if exam.max_points != max_points:
                    changes["max_points"] = {"old": exam.max_points, "new": max_points}
                    exam.max_points = max_points

            # Update weight
            if weight is not None:
                if not validate_weight(weight):
                    raise ValueError("Weight must be between 0 and 100")
                if exam.weight != weight:
                    changes["weight"] = {"old": exam.weight, "new": weight}
                    exam.weight = weight

            # Update description
            if description is not None:
                description = description.strip()
                if len(description) > 500:
                    raise ValueError("Description cannot exceed 500 characters")
                if exam.description != description:
                    changes["description"] = {"old": exam.description, "new": description}
                    exam.description = description

            if changes:
                self.commit()
                AuditService.log(
                    action="update",
                    target_type="Exam",
                    target_id=exam.id,
                    details=changes,
                )
                logger.info(f"Successfully updated exam: {exam.name}")
            return exam

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while updating exam: {e}")
            raise

    def delete_exam(self, exam_id: int) -> bool:
        """
        Delete an exam from the database.

        Args:
            exam_id: Exam database ID

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If exam not found
        """
        try:
            exam = self.query(Exam).filter_by(id=exam_id).first()

            if not exam:
                raise ValueError(f"Exam with ID {exam_id} not found")

            exam_name = exam.name
            exam_id_val = exam.id
            self.delete(exam)
            self.commit()

            # Log deletion
            AuditService.log(
                action="delete",
                target_type="Exam",
                target_id=exam_id_val,
                details={"name": exam_name},
            )

            logger.info(f"Successfully deleted exam: {exam_name}")
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while deleting exam: {e}")
            raise
