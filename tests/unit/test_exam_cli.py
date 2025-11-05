"""
Unit tests for exam CLI tool.

This module tests all exam management CLI functions.
"""

from datetime import datetime
import pytest

from cli.exam_cli import (
    add_exam,
    delete_exam,
    get_exam,
    list_exams,
    update_exam,
)
from app.models.exam import validate_weight, validate_max_points, validate_due_date
from app.models.university import University
from app.models.course import Course
import app as app_module


class TestValidationFunctions:
    """Test validation helper functions."""

    def test_validate_weight_valid(self):
        """Test that valid weights pass validation."""
        assert validate_weight(0.0) is True
        assert validate_weight(0.3) is True
        assert validate_weight(0.5) is True
        assert validate_weight(1.0) is True

    def test_validate_weight_invalid(self):
        """Test that invalid weights fail validation."""
        assert validate_weight(-0.1) is False
        assert validate_weight(1.1) is False
        assert validate_weight(2.0) is False
        assert validate_weight(-1.0) is False

    def test_validate_max_points_valid(self):
        """Test that valid max_points pass validation."""
        assert validate_max_points(1.0) is True
        assert validate_max_points(50.0) is True
        assert validate_max_points(100.0) is True
        assert validate_max_points(0.5) is True

    def test_validate_max_points_invalid(self):
        """Test that invalid max_points fail validation."""
        assert validate_max_points(0.0) is False
        assert validate_max_points(-10.0) is False
        assert validate_max_points(-0.1) is False

    def test_validate_due_date(self):
        """Test due date validation."""
        assert validate_due_date(None) is True
        assert validate_due_date(datetime(2024, 12, 31)) is True
        assert validate_due_date(datetime.now()) is True


class TestAddExam:
    """Test add_exam function."""

    @pytest.fixture
    def sample_course(self, app, db):
        """Create a sample course for testing."""
        with app.app_context():
            university = University(name="Test University", slug="test-university")
            app_module.db_session.add(university)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            course = Course(
                name="Test Course",
                slug="test-course",
                semester="2023_SoSe",
                university_id=university.id,
            )
            app_module.db_session.add(course)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]
            # Return the ID to avoid detached instance issues
            return course.id

    def test_add_exam_success(self, app, db, sample_course):
        """Test adding an exam successfully."""
        with app.app_context():
            exam = add_exam(
                name="Midterm Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=sample_course,
            )

            assert exam is not None
            assert exam.id is not None
            assert exam.name == "Midterm Exam"
            assert exam.exam_type == "midterm"
            assert exam.max_points == 100.0
            assert exam.weight == 0.3
            assert exam.course_id == sample_course
            assert exam.due_date is None

    def test_add_exam_with_due_date(self, app, db, sample_course):
        """Test adding an exam with a due date."""
        with app.app_context():
            due_date = datetime(2024, 6, 15, 23, 59, 59)
            exam = add_exam(
                name="Final Exam",
                exam_type="final",
                max_points=150.0,
                weight=0.5,
                course_id=sample_course,
                due_date=due_date,
            )

            assert exam is not None
            assert exam.due_date == due_date

    def test_add_exam_empty_name(self, app, db, sample_course):
        """Test that empty name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam name cannot be empty"):
                add_exam(
                    name="",
                    exam_type="midterm",
                    max_points=100.0,
                    weight=0.3,
                    course_id=sample_course,
                )

    def test_add_exam_empty_name_whitespace(self, app, db, sample_course):
        """Test that whitespace-only name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam name cannot be empty"):
                add_exam(
                    name="   ",
                    exam_type="midterm",
                    max_points=100.0,
                    weight=0.3,
                    course_id=sample_course,
                )

    def test_add_exam_name_too_long(self, app, db, sample_course):
        """Test that name exceeding 255 characters raises ValueError."""
        with app.app_context():
            long_name = "A" * 256
            with pytest.raises(ValueError, match="cannot exceed 255 characters"):
                add_exam(
                    name=long_name,
                    exam_type="midterm",
                    max_points=100.0,
                    weight=0.3,
                    course_id=sample_course,
                )

    def test_add_exam_empty_exam_type(self, app, db, sample_course):
        """Test that empty exam_type raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam type cannot be empty"):
                add_exam(
                    name="Test Exam",
                    exam_type="",
                    max_points=100.0,
                    weight=0.3,
                    course_id=sample_course,
                )

    def test_add_exam_invalid_max_points_zero(self, app, db, sample_course):
        """Test that zero max_points raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid max_points"):
                add_exam(
                    name="Test Exam",
                    exam_type="midterm",
                    max_points=0.0,
                    weight=0.3,
                    course_id=sample_course,
                )

    def test_add_exam_invalid_max_points_negative(self, app, db, sample_course):
        """Test that negative max_points raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid max_points"):
                add_exam(
                    name="Test Exam",
                    exam_type="midterm",
                    max_points=-10.0,
                    weight=0.3,
                    course_id=sample_course,
                )

    def test_add_exam_invalid_weight_negative(self, app, db, sample_course):
        """Test that negative weight raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid weight"):
                add_exam(
                    name="Test Exam",
                    exam_type="midterm",
                    max_points=100.0,
                    weight=-0.1,
                    course_id=sample_course,
                )

    def test_add_exam_invalid_weight_too_large(self, app, db, sample_course):
        """Test that weight > 1 raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid weight"):
                add_exam(
                    name="Test Exam",
                    exam_type="midterm",
                    max_points=100.0,
                    weight=1.5,
                    course_id=sample_course,
                )

    def test_add_exam_invalid_course_id(self, app, db):
        """Test that invalid course_id raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Course with ID 9999 not found"):
                add_exam(
                    name="Test Exam",
                    exam_type="midterm",
                    max_points=100.0,
                    weight=0.3,
                    course_id=9999,
                )

    def test_add_exam_case_normalization(self, app, db, sample_course):
        """Test that exam_type is normalized to lowercase."""
        with app.app_context():
            exam = add_exam(
                name="Test Exam",
                exam_type="MIDTERM",
                max_points=100.0,
                weight=0.3,
                course_id=sample_course,
            )

            assert exam.exam_type == "midterm"


class TestListExams:
    """Test list_exams function."""

    @pytest.fixture
    def sample_exams(self, app, db):
        """Create sample exams for testing."""
        with app.app_context():
            university = University(name="Test University", slug="test-university")
            app_module.db_session.add(university)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            course1 = Course(
                name="Course 1",
                slug="course-1",
                semester="2023_SoSe",
                university_id=university.id,
            )
            course2 = Course(
                name="Course 2",
                slug="course-2",
                semester="2023_WiSe",
                university_id=university.id,
            )
            app_module.db_session.add(course1)  # type: ignore[union-attr]
            app_module.db_session.add(course2)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            # Add exams using the CLI function
            add_exam(
                "Midterm Exam",
                "midterm",
                100.0,
                0.3,
                course1.id,
                datetime(2024, 3, 15),
            )
            add_exam(
                "Final Exam", "final", 150.0, 0.5, course1.id, datetime(2024, 6, 15)
            )
            add_exam("Quiz 1", "quiz", 50.0, 0.1, course2.id, datetime(2024, 2, 1))

            return {"course1_id": course1.id, "course2_id": course2.id}

    def test_list_exams_all(self, app, db, sample_exams):
        """Test listing all exams."""
        with app.app_context():
            exams = list_exams()
            assert len(exams) == 3

    def test_list_exams_filter_by_course(self, app, db, sample_exams):
        """Test filtering exams by course."""
        with app.app_context():
            exams = list_exams(course_id=sample_exams["course1_id"])
            assert len(exams) == 2
            assert all(exam.course_id == sample_exams["course1_id"] for exam in exams)

    def test_list_exams_filter_by_type(self, app, db, sample_exams):
        """Test filtering exams by exam type."""
        with app.app_context():
            exams = list_exams(exam_type="midterm")
            assert len(exams) == 1
            assert exams[0].exam_type == "midterm"

    def test_list_exams_filter_by_course_and_type(self, app, db, sample_exams):
        """Test filtering exams by both course and type."""
        with app.app_context():
            exams = list_exams(course_id=sample_exams["course1_id"], exam_type="final")
            assert len(exams) == 1
            assert exams[0].exam_type == "final"
            assert exams[0].course_id == sample_exams["course1_id"]

    def test_list_exams_empty_result(self, app, db, sample_exams):
        """Test that empty list is returned when no exams match."""
        with app.app_context():
            exams = list_exams(course_id=9999)
            assert exams == []

    def test_list_exams_ordering(self, app, db, sample_exams):
        """Test that exams are ordered by due date."""
        with app.app_context():
            exams = list_exams()
            # Should be ordered by due_date ascending
            assert exams[0].name == "Quiz 1"  # Feb 1
            assert exams[1].name == "Midterm Exam"  # Mar 15
            assert exams[2].name == "Final Exam"  # Jun 15


class TestGetExam:
    """Test get_exam function."""

    @pytest.fixture
    def sample_exam(self, app, db):
        """Create a sample exam for testing."""
        with app.app_context():
            university = University(name="Test University", slug="test-university")
            app_module.db_session.add(university)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            course = Course(
                name="Test Course",
                slug="test-course",
                semester="2023_SoSe",
                university_id=university.id,
            )
            app_module.db_session.add(course)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            exam = add_exam("Midterm Exam", "midterm", 100.0, 0.3, course.id)
            return exam.id  # type: ignore[union-attr]

    def test_get_exam_success(self, app, db, sample_exam):
        """Test getting an exam successfully."""
        with app.app_context():
            exam = get_exam(sample_exam)

            assert exam is not None
            assert exam.id == sample_exam
            assert exam.name == "Midterm Exam"

    def test_get_exam_not_found(self, app, db):
        """Test getting non-existent exam returns None."""
        with app.app_context():
            exam = get_exam(9999)
            assert exam is None


class TestUpdateExam:
    """Test update_exam function."""

    @pytest.fixture
    def sample_exam(self, app, db):
        """Create a sample exam for testing."""
        with app.app_context():
            university = University(name="Test University", slug="test-university")
            app_module.db_session.add(university)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            course = Course(
                name="Test Course",
                slug="test-course",
                semester="2023_SoSe",
                university_id=university.id,
            )
            app_module.db_session.add(course)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            exam = add_exam("Midterm Exam", "midterm", 100.0, 0.3, course.id)
            return exam.id  # type: ignore[union-attr]

    def test_update_exam_name(self, app, db, sample_exam):
        """Test updating exam name."""
        with app.app_context():
            exam = update_exam(sample_exam, name="Updated Midterm")

            assert exam is not None
            assert exam.name == "Updated Midterm"

    def test_update_exam_type(self, app, db, sample_exam):
        """Test updating exam type."""
        with app.app_context():
            exam = update_exam(sample_exam, exam_type="quiz")

            assert exam is not None
            assert exam.exam_type == "quiz"

    def test_update_exam_max_points(self, app, db, sample_exam):
        """Test updating max_points."""
        with app.app_context():
            exam = update_exam(sample_exam, max_points=120.0)

            assert exam is not None
            assert exam.max_points == 120.0

    def test_update_exam_weight(self, app, db, sample_exam):
        """Test updating weight."""
        with app.app_context():
            exam = update_exam(sample_exam, weight=0.4)

            assert exam is not None
            assert exam.weight == 0.4

    def test_update_exam_due_date(self, app, db, sample_exam):
        """Test updating due date."""
        with app.app_context():
            new_due_date = datetime(2024, 12, 31)
            exam = update_exam(sample_exam, due_date=new_due_date)

            assert exam is not None
            assert exam.due_date == new_due_date

    def test_update_exam_clear_due_date(self, app, db, sample_exam):
        """Test clearing due date."""
        with app.app_context():
            # First add a due date
            update_exam(sample_exam, due_date=datetime(2024, 12, 31))
            # Then clear it
            exam = update_exam(sample_exam, clear_due_date=True)

            assert exam is not None
            assert exam.due_date is None

    def test_update_exam_not_found(self, app, db):
        """Test updating non-existent exam raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam with ID 9999 not found"):
                update_exam(9999, name="Updated Name")

    def test_update_exam_invalid_name_empty(self, app, db, sample_exam):
        """Test updating with empty name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam name cannot be empty"):
                update_exam(sample_exam, name="   ")

    def test_update_exam_invalid_max_points(self, app, db, sample_exam):
        """Test updating with invalid max_points raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid max_points"):
                update_exam(sample_exam, max_points=0.0)

    def test_update_exam_invalid_weight(self, app, db, sample_exam):
        """Test updating with invalid weight raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid weight"):
                update_exam(sample_exam, weight=1.5)

    def test_update_exam_multiple_fields(self, app, db, sample_exam):
        """Test updating multiple fields at once."""
        with app.app_context():
            exam = update_exam(
                sample_exam,
                name="Updated Exam",
                exam_type="final",
                max_points=150.0,
                weight=0.5,
            )

            assert exam is not None
            assert exam.name == "Updated Exam"
            assert exam.exam_type == "final"
            assert exam.max_points == 150.0
            assert exam.weight == 0.5


class TestDeleteExam:
    """Test delete_exam function."""

    @pytest.fixture
    def sample_exam(self, app, db):
        """Create a sample exam for testing."""
        with app.app_context():
            university = University(name="Test University", slug="test-university")
            app_module.db_session.add(university)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            course = Course(
                name="Test Course",
                slug="test-course",
                semester="2023_SoSe",
                university_id=university.id,
            )
            app_module.db_session.add(course)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            exam = add_exam("Midterm Exam", "midterm", 100.0, 0.3, course.id)
            return exam.id  # type: ignore[union-attr]

    def test_delete_exam_success(self, app, db, sample_exam):
        """Test deleting an exam successfully."""
        with app.app_context():
            result = delete_exam(sample_exam)
            assert result is True

            # Verify exam is deleted
            exam = get_exam(sample_exam)
            assert exam is None

    def test_delete_exam_not_found(self, app, db):
        """Test deleting non-existent exam raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam with ID 9999 not found"):
                delete_exam(9999)
