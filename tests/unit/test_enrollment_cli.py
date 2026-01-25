"""
Unit tests for enrollment CLI tool.

Tests all CRUD operations for enrollment management.
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.university import University
from app.services.enrollment_service import EnrollmentService


@pytest.fixture
def service():
    """Return an EnrollmentService instance."""
    return EnrollmentService()


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

    def test_add_enrollment_success(
        self, app, db, service, sample_student, sample_course
    ):
        """Test adding a new enrollment."""
        with app.app_context():
            enrollment = service.add_enrollment(
                sample_student["student_id"], sample_course
            )

            # Verify enrollment was created
            assert enrollment is not None
            assert isinstance(enrollment, Enrollment)
            assert enrollment.student_id == sample_student["id"]
            assert enrollment.course_id == sample_course
            assert enrollment.status == "active"
            assert enrollment.enrollment_date == date.today()
            assert enrollment.unenrollment_date is None

    def test_add_enrollment_student_not_found(self, app, db, service, sample_course):
        """Test adding enrollment with non-existent student."""
        with app.app_context():
            with pytest.raises(ValueError, match="nicht gefunden"):
                service.add_enrollment("99999999", sample_course)

    def test_add_enrollment_course_not_found(self, app, db, service, sample_student):
        """Test adding enrollment with non-existent course."""
        with app.app_context():
            with pytest.raises(ValueError, match="Course with ID 99999 not found"):
                service.add_enrollment(sample_student["student_id"], 99999)

    def test_add_enrollment_duplicate(
        self, app, db, service, sample_student, sample_course
    ):
        """Test adding duplicate enrollment."""
        with app.app_context():
            # Add first enrollment
            enrollment = service.add_enrollment(
                sample_student["student_id"], sample_course
            )
            assert enrollment is not None

            # Try to add duplicate
            with pytest.raises(IntegrityError, match="already enrolled"):
                service.add_enrollment(sample_student["student_id"], sample_course)

    def test_list_enrollments_by_course(
        self, app, db, service, sample_student, sample_course
    ):
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
            enrollments = service.list_enrollments(course_id=sample_course)
            assert isinstance(enrollments, list)
            assert len(enrollments) == 1
            assert enrollments[0].course_id == sample_course

    def test_list_enrollments_by_student(
        self, app, db, service, sample_student, sample_course
    ):
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
            enrollments = service.list_enrollments(
                student_id_str=sample_student["student_id"]
            )
            assert isinstance(enrollments, list)
            assert len(enrollments) == 1
            assert enrollments[0].student_id == sample_student["id"]

    def test_list_enrollments_student_not_found(self, app, db, service):
        """Test listing enrollments for non-existent student."""
        with app.app_context():
            with pytest.raises(ValueError, match="nicht gefunden"):
                service.list_enrollments(student_id_str="99999999")

    def test_list_enrollments_empty(self, app, db, service, sample_course):
        """Test listing enrollments when none exist."""
        with app.app_context():
            enrollments = service.list_enrollments(course_id=sample_course)
            assert isinstance(enrollments, list)
            assert len(enrollments) == 0

    def test_remove_enrollment_success(
        self, app, db, service, sample_student, sample_course
    ):
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
            result = service.remove_enrollment(
                sample_student["student_id"], sample_course
            )
            assert result is True

            # Verify enrollment was removed
            enrollment = (
                db.session.query(Enrollment)
                .filter_by(student_id=sample_student["id"], course_id=sample_course)
                .first()
            )
            assert enrollment is None

    def test_remove_enrollment_student_not_found(self, app, db, service, sample_course):
        """Test removing enrollment with non-existent student."""
        with app.app_context():
            with pytest.raises(ValueError, match="nicht gefunden"):
                service.remove_enrollment("99999999", sample_course)

    def test_remove_enrollment_not_found(
        self, app, db, service, sample_student, sample_course
    ):
        """Test removing enrollment that doesn't exist."""
        with app.app_context():
            with pytest.raises(ValueError, match="No enrollment found"):
                service.remove_enrollment(sample_student["student_id"], sample_course)

    def test_update_enrollment_status_success(
        self, app, db, service, sample_student, sample_course
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
            updated_enrollment = service.update_enrollment_status(
                sample_student["student_id"], sample_course, "completed"
            )
            assert updated_enrollment is not None
            assert isinstance(updated_enrollment, Enrollment)
            assert updated_enrollment.status == "completed"

    def test_update_enrollment_status_to_dropped(
        self, app, db, service, sample_student, sample_course
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
            updated_enrollment = service.update_enrollment_status(
                sample_student["student_id"], sample_course, "dropped"
            )
            assert updated_enrollment is not None
            assert isinstance(updated_enrollment, Enrollment)
            assert updated_enrollment.status == "dropped"
            assert updated_enrollment.unenrollment_date == date.today()

    def test_update_enrollment_status_invalid(
        self, app, db, service, sample_student, sample_course
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
            with pytest.raises(ValueError, match="Invalid status"):
                service.update_enrollment_status(
                    sample_student["student_id"], sample_course, "invalid_status"
                )

    def test_update_enrollment_status_student_not_found(
        self, app, db, service, sample_course
    ):
        """Test updating enrollment status with non-existent student."""
        with app.app_context():
            with pytest.raises(ValueError, match="nicht gefunden"):
                service.update_enrollment_status("99999999", sample_course, "completed")

    def test_update_enrollment_status_enrollment_not_found(
        self, app, db, service, sample_student, sample_course
    ):
        """Test updating enrollment status when enrollment doesn't exist."""
        with app.app_context():
            with pytest.raises(ValueError, match="No enrollment found"):
                service.update_enrollment_status(
                    sample_student["student_id"], sample_course, "completed"
                )

    def test_enrollment_model_repr(
        self, app, db, service, sample_student, sample_course
    ):
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

    def test_enrollment_relationships(
        self, app, db, service, sample_student, sample_course
    ):
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
        self, app, db, service, sample_student, sample_university
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
            enrollment1 = service.add_enrollment(
                sample_student["student_id"], course1.id
            )
            enrollment2 = service.add_enrollment(
                sample_student["student_id"], course2.id
            )

            assert enrollment1 is not None
            assert enrollment2 is not None

            # Verify both enrollments exist
            enrollments = (
                db.session.query(Enrollment)
                .filter_by(student_id=sample_student["id"])
                .all()
            )
            assert len(enrollments) == 2

    def test_multiple_students_in_course(self, app, db, service, sample_course):
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
            enrollment1 = service.add_enrollment("11111111", sample_course)
            enrollment2 = service.add_enrollment("22222222", sample_course)

            assert enrollment1 is not None
            assert enrollment2 is not None

            # Verify both enrollments exist
            enrollments = (
                db.session.query(Enrollment).filter_by(course_id=sample_course).all()
            )
            assert len(enrollments) == 2
