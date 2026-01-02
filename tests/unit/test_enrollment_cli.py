"""
Unit tests for enrollment CLI tool.

Tests all CRUD operations for enrollment management.
"""

import pytest
from datetime import date

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.university import University
from cli.enrollment_cli import (
    add_enrollment,
    list_enrollments,
    remove_enrollment,
    update_enrollment_status,
)


class TestEnrollmentCLI:
    """Test cases for enrollment CLI operations."""

    @pytest.fixture
    def sample_university(self, app, db):
        """Create a sample university for testing."""
        with app.app_context():
            university = University(name="Test University", slug="test-university")
            db.session.add(university)
            db.session.commit()
            # Return the ID, not the object
            return university.id

    @pytest.fixture
    def sample_course(self, app, db, sample_university):
        """Create a sample course for testing."""
        with app.app_context():
            course = Course(
                name="Test Course",
                slug="test-course",
                semester="2023_SoSe",
                university_id=sample_university,
            )
            db.session.add(course)
            db.session.commit()
            # Return the ID, not the object
            return course.id

    @pytest.fixture
    def sample_student(self, app, db):
        """Create a sample student for testing."""
        with app.app_context():
            student = Student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Computer Science",
            )
            db.session.add(student)
            db.session.commit()
            # Return both ID and student_id for testing
            return {"id": student.id, "student_id": student.student_id}

    def test_add_enrollment_success(self, app, db, sample_student, sample_course):
        """Test adding a new enrollment."""
        with app.app_context():
            result = add_enrollment(sample_student["student_id"], sample_course)
            assert result == 0

            # Verify enrollment was created
            enrollment = (
                db.session.query(Enrollment)
                .filter_by(student_id=sample_student["id"], course_id=sample_course)
                .first()
            )
            assert enrollment is not None
            assert enrollment.status == "active"
            assert enrollment.enrollment_date == date.today()
            assert enrollment.unenrollment_date is None

    def test_add_enrollment_student_not_found(self, app, db, sample_course):
        """Test adding enrollment with non-existent student."""
        with app.app_context():
            result = add_enrollment("99999999", sample_course)
            assert result == 1

    def test_add_enrollment_course_not_found(self, app, db, sample_student):
        """Test adding enrollment with non-existent course."""
        with app.app_context():
            result = add_enrollment(sample_student["student_id"], 99999)
            assert result == 1

    def test_add_enrollment_duplicate(self, app, db, sample_student, sample_course):
        """Test adding duplicate enrollment."""
        with app.app_context():
            # Add first enrollment
            result = add_enrollment(sample_student["student_id"], sample_course)
            assert result == 0

            # Try to add duplicate
            result = add_enrollment(sample_student["student_id"], sample_course)
            assert result == 1

    def test_list_enrollments_by_course(self, app, db, sample_student, sample_course):
        """Test listing enrollments for a specific course."""
        with app.app_context():
            # Create enrollment
            enrollment = Enrollment(
                student_id=sample_student["id"],
                course_id=sample_course,
                status="active",
            )
            db.session.add(enrollment)
            db.session.commit()

            # List enrollments
            result = list_enrollments(course_id=sample_course)
            assert result == 0

    def test_list_enrollments_by_student(self, app, db, sample_student, sample_course):
        """Test listing enrollments for a specific student."""
        with app.app_context():
            # Create enrollment
            enrollment = Enrollment(
                student_id=sample_student["id"],
                course_id=sample_course,
                status="active",
            )
            db.session.add(enrollment)
            db.session.commit()

            # List enrollments
            result = list_enrollments(student_id_str=sample_student["student_id"])
            assert result == 0

    def test_list_enrollments_student_not_found(self, app, db):
        """Test listing enrollments for non-existent student."""
        with app.app_context():
            result = list_enrollments(student_id_str="99999999")
            assert result == 1

    def test_list_enrollments_empty(self, app, db, sample_course):
        """Test listing enrollments when none exist."""
        with app.app_context():
            result = list_enrollments(course_id=sample_course)
            assert result == 0

    def test_remove_enrollment_success(self, app, db, sample_student, sample_course):
        """Test removing an enrollment."""
        with app.app_context():
            # Create enrollment
            enrollment = Enrollment(
                student_id=sample_student["id"],
                course_id=sample_course,
                status="active",
            )
            db.session.add(enrollment)
            db.session.commit()

            # Remove enrollment
            result = remove_enrollment(sample_student["student_id"], sample_course)
            assert result == 0

            # Verify enrollment was removed
            enrollment = (
                db.session.query(Enrollment)
                .filter_by(student_id=sample_student["id"], course_id=sample_course)
                .first()
            )
            assert enrollment is None

    def test_remove_enrollment_student_not_found(self, app, db, sample_course):
        """Test removing enrollment with non-existent student."""
        with app.app_context():
            result = remove_enrollment("99999999", sample_course)
            assert result == 1

    def test_remove_enrollment_not_found(self, app, db, sample_student, sample_course):
        """Test removing enrollment that doesn't exist."""
        with app.app_context():
            result = remove_enrollment(sample_student["student_id"], sample_course)
            assert result == 1

    def test_update_enrollment_status_success(
        self, app, db, sample_student, sample_course
    ):
        """Test updating enrollment status."""
        with app.app_context():
            # Create enrollment
            enrollment = Enrollment(
                student_id=sample_student["id"],
                course_id=sample_course,
                status="active",
            )
            db.session.add(enrollment)
            db.session.commit()

            # Update status
            result = update_enrollment_status(
                sample_student["student_id"], sample_course, "completed"
            )
            assert result == 0

            # Verify status was updated
            enrollment = (
                db.session.query(Enrollment)
                .filter_by(student_id=sample_student["id"], course_id=sample_course)
                .first()
            )
            assert enrollment.status == "completed"

    def test_update_enrollment_status_to_dropped(
        self, app, db, sample_student, sample_course
    ):
        """Test updating enrollment status to dropped sets unenrollment_date."""
        with app.app_context():
            # Create enrollment
            enrollment = Enrollment(
                student_id=sample_student["id"],
                course_id=sample_course,
                status="active",
            )
            db.session.add(enrollment)
            db.session.commit()

            # Update status to dropped
            result = update_enrollment_status(
                sample_student["student_id"], sample_course, "dropped"
            )
            assert result == 0

            # Verify status and unenrollment_date were updated
            enrollment = (
                db.session.query(Enrollment)
                .filter_by(student_id=sample_student["id"], course_id=sample_course)
                .first()
            )
            assert enrollment.status == "dropped"
            assert enrollment.unenrollment_date == date.today()

    def test_update_enrollment_status_invalid(
        self, app, db, sample_student, sample_course
    ):
        """Test updating enrollment status with invalid status."""
        with app.app_context():
            # Create enrollment
            enrollment = Enrollment(
                student_id=sample_student["id"],
                course_id=sample_course,
                status="active",
            )
            db.session.add(enrollment)
            db.session.commit()

            # Try to update with invalid status
            result = update_enrollment_status(
                sample_student["student_id"], sample_course, "invalid_status"
            )
            assert result == 1

    def test_update_enrollment_status_student_not_found(self, app, db, sample_course):
        """Test updating enrollment status with non-existent student."""
        with app.app_context():
            result = update_enrollment_status("99999999", sample_course, "completed")
            assert result == 1

    def test_update_enrollment_status_enrollment_not_found(
        self, app, db, sample_student, sample_course
    ):
        """Test updating enrollment status when enrollment doesn't exist."""
        with app.app_context():
            result = update_enrollment_status(
                sample_student["student_id"], sample_course, "completed"
            )
            assert result == 1

    def test_enrollment_model_repr(self, app, db, sample_student, sample_course):
        """Test Enrollment model string representation."""
        with app.app_context():
            enrollment = Enrollment(
                student_id=sample_student["id"],
                course_id=sample_course,
                status="active",
            )
            db.session.add(enrollment)
            db.session.commit()

            assert "Enrollment" in repr(enrollment)
            assert str(sample_student["id"]) in repr(enrollment)
            assert str(sample_course) in repr(enrollment)
            assert "active" in repr(enrollment)

    def test_enrollment_relationships(self, app, db, sample_student, sample_course):
        """Test that enrollment relationships are properly established."""
        with app.app_context():
            enrollment = Enrollment(
                student_id=sample_student["id"],
                course_id=sample_course,
                status="active",
            )
            db.session.add(enrollment)
            db.session.commit()

            # Refresh to load relationships
            db.session.refresh(enrollment)

            # Test student relationship
            assert enrollment.student is not None
            assert enrollment.student.student_id == sample_student["student_id"]

            # Test course relationship
            assert enrollment.course is not None
            assert enrollment.course.id == sample_course

    def test_multiple_enrollments_for_student(
        self, app, db, sample_student, sample_university
    ):
        """Test that a student can enroll in multiple courses."""
        with app.app_context():
            # Create two courses
            course1 = Course(
                name="Course 1",
                slug="course-1",
                semester="2023_SoSe",
                university_id=sample_university,
            )
            course2 = Course(
                name="Course 2",
                slug="course-2",
                semester="2023_SoSe",
                university_id=sample_university,
            )
            db.session.add(course1)
            db.session.add(course2)
            db.session.commit()

            # Enroll in both courses
            result1 = add_enrollment(sample_student["student_id"], course1.id)
            result2 = add_enrollment(sample_student["student_id"], course2.id)

            assert result1 == 0
            assert result2 == 0

            # Verify both enrollments exist
            enrollments = (
                db.session.query(Enrollment)
                .filter_by(student_id=sample_student["id"])
                .all()
            )
            assert len(enrollments) == 2

    def test_multiple_students_in_course(self, app, db, sample_course):
        """Test that multiple students can enroll in the same course."""
        with app.app_context():
            # Create two students
            student1 = Student(
                first_name="Student",
                last_name="One",
                student_id="11111111",
                email="student1@example.com",
                program="CS",
            )
            student2 = Student(
                first_name="Student",
                last_name="Two",
                student_id="22222222",
                email="student2@example.com",
                program="CS",
            )
            db.session.add(student1)
            db.session.add(student2)
            db.session.commit()

            # Enroll both students
            result1 = add_enrollment("11111111", sample_course)
            result2 = add_enrollment("22222222", sample_course)

            assert result1 == 0
            assert result2 == 0

            # Verify both enrollments exist
            enrollments = (
                db.session.query(Enrollment).filter_by(course_id=sample_course).all()
            )
            assert len(enrollments) == 2
