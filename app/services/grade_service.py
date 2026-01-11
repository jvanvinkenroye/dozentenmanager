"""
Grade service for business logic layer.

This module provides business logic for grade management, including
grade creation, updates, statistics, and weighted average calculations.
"""

import logging

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

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
from app.services.base_service import BaseService

# Configure logging
logger = logging.getLogger(__name__)


class GradeService(BaseService):
    """
    Service class for grade management.

    Provides methods for creating, updating, deleting grades, calculating
    weighted averages, and managing exam components and grading scales.
    """

    def add_grade(
        self,
        enrollment_id: int,
        exam_id: int,
        points: float,
        component_id: int | None = None,
        graded_by: str | None = None,
        is_final: bool = False,
        notes: str | None = None,
    ) -> Grade:
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
            Created Grade object

        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraint fails
        """
        # Validate enrollment exists
        enrollment = self.query(Enrollment).filter_by(id=enrollment_id).first()
        if not enrollment:
            raise ValueError(f"Enrollment with ID {enrollment_id} not found")

        # Validate exam exists
        exam = self.query(Exam).filter_by(id=exam_id).first()
        if not exam:
            raise ValueError(f"Exam with ID {exam_id} not found")

        # Get max points from component or exam
        if component_id:
            component = self.query(ExamComponent).filter_by(id=component_id).first()
            if not component:
                raise ValueError(f"ExamComponent with ID {component_id} not found")
            if component.exam_id != exam_id:
                raise ValueError(
                    f"Component {component_id} does not belong to exam {exam_id}"
                )
            max_points = component.max_points
        else:
            max_points = exam.max_points

        # Validate points
        if not validate_points(points, max_points):
            raise ValueError(f"Points must be between 0 and {max_points}")

        # Check for existing grade
        existing = (
            self.query(Grade)
            .filter_by(
                enrollment_id=enrollment_id,
                exam_id=exam_id,
                component_id=component_id,
            )
            .first()
        )
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
            self.add(grade)
            self.commit()

            logger.info(
                f"Grade added: {grade.points}/{max_points} = {grade.percentage}% "
                f"({grade.grade_value} - {grade.grade_label})"
            )
            return grade

        except IntegrityError as e:
            self.rollback()
            logger.error(f"Database constraint error while adding grade: {e}")
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while adding grade: {e}")
            raise ValueError(f"Failed to add grade: {e}") from e

    def update_grade(
        self,
        grade_id: int,
        points: float | None = None,
        is_final: bool | None = None,
        notes: str | None = None,
        graded_by: str | None = None,
    ) -> Grade:
        """
        Update an existing grade.

        Args:
            grade_id: Grade ID to update
            points: New points (will recalculate percentage and grade)
            is_final: New final status
            notes: New notes
            graded_by: Who updated the grade

        Returns:
            Updated Grade object

        Raises:
            ValueError: If validation fails
        """
        grade = self.query(Grade).filter_by(id=grade_id).first()
        if not grade:
            raise ValueError(f"Grade with ID {grade_id} not found")

        try:
            if points is not None:
                # Get max points
                if grade.component_id:
                    component = (
                        self.query(ExamComponent)
                        .filter_by(id=grade.component_id)
                        .first()
                    )
                    max_points = component.max_points
                else:
                    exam = self.query(Exam).filter_by(id=grade.exam_id).first()
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

            self.commit()
            logger.info(f"Grade {grade_id} updated successfully")
            return grade

        except ValueError:
            # Re-raise validation errors
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while updating grade: {e}")
            raise ValueError(f"Failed to update grade: {e}") from e

    def delete_grade(self, grade_id: int) -> bool:
        """
        Delete a grade.

        Args:
            grade_id: Grade ID to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If grade not found
        """
        grade = self.query(Grade).filter_by(id=grade_id).first()
        if not grade:
            raise ValueError(f"Grade with ID {grade_id} not found")

        try:
            self.delete(grade)
            self.commit()
            logger.info(f"Grade {grade_id} deleted")
            return True

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while deleting grade: {e}")
            raise ValueError(f"Failed to delete grade: {e}") from e

    def get_grade(self, grade_id: int) -> Grade:
        """
        Get a grade by ID.

        Args:
            grade_id: Grade ID

        Returns:
            Grade object

        Raises:
            ValueError: If grade not found
        """
        grade = self.query(Grade).filter_by(id=grade_id).first()
        if not grade:
            raise ValueError(f"Grade with ID {grade_id} not found")
        return grade

    def list_grades(
        self,
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
        try:
            query = self.query(Grade)

            if enrollment_id:
                query = query.filter(Grade.enrollment_id == enrollment_id)

            if exam_id:
                query = query.filter(Grade.exam_id == exam_id)

            if course_id:
                query = query.join(Enrollment).filter(Enrollment.course_id == course_id)

            if is_final is not None:
                query = query.filter(Grade.is_final == is_final)

            return query.order_by(Grade.graded_at.desc()).all()

        except SQLAlchemyError as e:
            logger.error(f"Database error while listing grades: {e}")
            return []

    def calculate_weighted_average(
        self, enrollment_id: int, course_id: int | None = None
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
        enrollment = self.query(Enrollment).filter_by(id=enrollment_id).first()
        if not enrollment:
            return None

        # Get all final grades for the enrollment
        query = self.query(Grade).filter(
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
        exam_grades: dict = {}

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
                exam_grades[exam.id]["components"].append(
                    {
                        "component_name": grade.component.name,
                        "points": grade.points,
                        "percentage": grade.percentage,
                        "grade": grade.grade_value,
                    }
                )
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

    def get_exam_statistics(self, exam_id: int) -> dict | None:
        """
        Calculate statistics for an exam.

        Args:
            exam_id: Exam ID

        Returns:
            Dictionary with statistics or None if no grades
        """
        exam = self.query(Exam).filter_by(id=exam_id).first()
        if not exam:
            return None

        grades = (
            self.query(Grade)
            .filter(
                Grade.exam_id == exam_id,
                Grade.component_id == None,  # noqa: E711 - Only exam-level grades
            )
            .all()
        )

        if not grades:
            return None

        points_list = [g.points for g in grades]
        percentage_list = [g.percentage for g in grades]
        grade_values = [g.grade_value for g in grades]

        # Count grade distribution
        grade_distribution: dict[str, int] = {}
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
        self,
        exam_id: int,
        name: str,
        weight: float,
        max_points: float,
        order: int = 0,
        description: str | None = None,
    ) -> ExamComponent:
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
            Created ExamComponent

        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraint fails
        """
        exam = self.query(Exam).filter_by(id=exam_id).first()
        if not exam:
            raise ValueError(f"Exam with ID {exam_id} not found")

        if weight <= 0 or weight > 100:
            raise ValueError("Weight must be between 0 (exclusive) and 100")

        if max_points <= 0:
            raise ValueError("Max points must be greater than 0")

        # Check total weight doesn't exceed 100%
        existing_weight = (
            self.query(func.sum(ExamComponent.weight))
            .filter(ExamComponent.exam_id == exam_id)
            .scalar()
            or 0
        )

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
            self.add(component)
            self.commit()

            logger.info(f"Added component '{name}' to exam {exam_id}")
            return component

        except IntegrityError as e:
            self.rollback()
            logger.error(f"Database constraint error while adding component: {e}")
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while adding component: {e}")
            raise ValueError(f"Failed to add component: {e}") from e

    def list_exam_components(self, exam_id: int) -> list[ExamComponent]:
        """
        List all components for an exam.

        Args:
            exam_id: Exam ID

        Returns:
            List of ExamComponent objects ordered by display order
        """
        try:
            return (
                self.query(ExamComponent)
                .filter_by(exam_id=exam_id)
                .order_by(ExamComponent.order)
                .all()
            )

        except SQLAlchemyError as e:
            logger.error(f"Database error while listing exam components: {e}")
            return []

    def create_default_grading_scale(
        self, university_id: int | None = None
    ) -> GradingScale:
        """
        Create the default German grading scale.

        Args:
            university_id: Optional university to associate with

        Returns:
            Created GradingScale

        Raises:
            ValueError: If creation fails
        """
        try:
            scale = GradingScale(
                name="Deutsche Notenskala",
                university_id=university_id,
                is_default=True,
                description="Standard German grading scale (1.0 - 5.0)",
            )
            self.add(scale)
            self.db.session.flush()

            # Add thresholds
            for grade_value, (min_pct, max_pct, description) in GERMAN_GRADES.items():
                threshold = GradeThreshold(
                    scale_id=scale.id,
                    grade_value=grade_value,
                    grade_label=description,
                    min_percentage=min_pct,
                    description=f"{min_pct}-{max_pct}%",
                )
                self.add(threshold)

            self.commit()
            logger.info(f"Created default German grading scale (ID: {scale.id})")
            return scale

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while creating grading scale: {e}")
            raise ValueError(f"Failed to create grading scale: {e}") from e
