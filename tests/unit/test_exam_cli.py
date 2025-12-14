"""
Unit tests for exam CLI tool.

This module tests all exam management CLI functions.
"""

import pytest
from datetime import date

from cli.exam_cli import (
    add_exam,
    delete_exam,
    get_exam,
    list_exams,
    update_exam,
)
from cli.course_cli import add_course
from cli.university_cli import add_university
from app.models.exam import validate_weight, validate_max_points


class TestValidationFunctions:
    """Test validation helper functions."""

    def test_validate_weight_valid(self):
        """Test that valid weights pass validation."""
        assert validate_weight(0.0) is True
        assert validate_weight(0.5) is True
        assert validate_weight(1.0) is True
        assert validate_weight(0.25) is True
        assert validate_weight(0.75) is True

    def test_validate_weight_invalid(self):
        """Test that invalid weights fail validation."""
        assert validate_weight(-0.1) is False
        assert validate_weight(1.1) is False
        assert validate_weight(-1.0) is False
        assert validate_weight(2.0) is False

    def test_validate_max_points_valid(self):
        """Test that valid max_points pass validation."""
        assert validate_max_points(100.0) is True
        assert validate_max_points(0.5) is True
        assert validate_max_points(1000.0) is True
        assert validate_max_points(0.1) is True

    def test_validate_max_points_invalid(self):
        """Test that invalid max_points fail validation."""
        assert validate_max_points(0.0) is False
        assert validate_max_points(-0.1) is False
        assert validate_max_points(-100.0) is False


class TestAddExam:
    """Test add_exam function."""

    @pytest.fixture
    def sample_course(self, app, db):
        """Create a sample course for testing."""
        with app.app_context():
            university = add_university("Test University")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            # Return the ID to avoid detached instance issues
            return course.id

    def test_add_exam_success(self, app, db, sample_course):
        """Test adding an exam successfully."""
        with app.app_context():
            exam = add_exam(
                name="Midterm Exam",
                max_points=100.0,
                weight=0.4,
                course_id=sample_course,
            )

            assert exam is not None
            assert exam.id is not None
            assert exam.name == "Midterm Exam"
            assert exam.max_points == 100.0
            assert exam.weight == 0.4
            assert exam.course_id == sample_course
            assert exam.description is None
            assert exam.exam_date is None
            assert exam.due_date is None

    def test_add_exam_with_optional_fields(self, app, db, sample_course):
        """Test adding an exam with all optional fields."""
        with app.app_context():
            exam_date = date(2024, 3, 15)
            due_date = date(2024, 3, 20)

            exam = add_exam(
                name="Final Exam",
                max_points=150.0,
                weight=0.6,
                course_id=sample_course,
                description="Comprehensive final examination",
                exam_date=exam_date,
                due_date=due_date,
            )

            assert exam is not None
            assert exam.name == "Final Exam"
            assert exam.description == "Comprehensive final examination"
            assert exam.exam_date == exam_date
            assert exam.due_date == due_date

    def test_add_exam_empty_name(self, app, db, sample_course):
        """Test that adding an exam with empty name fails."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam name cannot be empty"):
                add_exam(
                    name="",
                    max_points=100.0,
                    weight=0.5,
                    course_id=sample_course,
                )

    def test_add_exam_name_too_long(self, app, db, sample_course):
        """Test that adding an exam with name > 255 chars fails."""
        with app.app_context():
            long_name = "x" * 256
            with pytest.raises(ValueError, match="cannot exceed 255 characters"):
                add_exam(
                    name=long_name,
                    max_points=100.0,
                    weight=0.5,
                    course_id=sample_course,
                )

    def test_add_exam_invalid_max_points_zero(self, app, db, sample_course):
        """Test that adding an exam with zero max_points fails."""
        with app.app_context():
            with pytest.raises(ValueError, match="Max points must be positive"):
                add_exam(
                    name="Test Exam",
                    max_points=0.0,
                    weight=0.5,
                    course_id=sample_course,
                )

    def test_add_exam_invalid_max_points_negative(self, app, db, sample_course):
        """Test that adding an exam with negative max_points fails."""
        with app.app_context():
            with pytest.raises(ValueError, match="Max points must be positive"):
                add_exam(
                    name="Test Exam",
                    max_points=-10.0,
                    weight=0.5,
                    course_id=sample_course,
                )

    def test_add_exam_invalid_weight_too_low(self, app, db, sample_course):
        """Test that adding an exam with weight < 0 fails."""
        with app.app_context():
            with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
                add_exam(
                    name="Test Exam",
                    max_points=100.0,
                    weight=-0.1,
                    course_id=sample_course,
                )

    def test_add_exam_invalid_weight_too_high(self, app, db, sample_course):
        """Test that adding an exam with weight > 1 fails."""
        with app.app_context():
            with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
                add_exam(
                    name="Test Exam",
                    max_points=100.0,
                    weight=1.5,
                    course_id=sample_course,
                )

    def test_add_exam_nonexistent_course(self, app, db):
        """Test that adding an exam for nonexistent course fails."""
        with app.app_context():
            with pytest.raises(ValueError, match="Course with ID 99999 not found"):
                add_exam(
                    name="Test Exam",
                    max_points=100.0,
                    weight=0.5,
                    course_id=99999,
                )

    def test_add_exam_description_too_long(self, app, db, sample_course):
        """Test that adding an exam with description > 5000 chars fails."""
        with app.app_context():
            long_description = "x" * 5001
            with pytest.raises(ValueError, match="Description cannot exceed 5000 characters"):
                add_exam(
                    name="Test Exam",
                    max_points=100.0,
                    weight=0.5,
                    course_id=sample_course,
                    description=long_description,
                )

    def test_add_exam_exam_date_after_due_date(self, app, db, sample_course):
        """Test that exam_date after due_date fails."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam date cannot be after due date"):
                add_exam(
                    name="Test Exam",
                    max_points=100.0,
                    weight=0.5,
                    course_id=sample_course,
                    exam_date=date(2024, 3, 20),
                    due_date=date(2024, 3, 15),
                )


class TestListExams:
    """Test list_exams function."""

    @pytest.fixture
    def sample_courses_with_exams(self, app, db):
        """Create sample courses with exams for testing."""
        with app.app_context():
            university = add_university("Test University")
            course1 = add_course(
                name="Course 1",
                semester="2024_WiSe",
                university_id=university.id,
            )
            course2 = add_course(
                name="Course 2",
                semester="2024_WiSe",
                university_id=university.id,
            )

            # Add exams to course 1
            add_exam(
                name="Midterm 1",
                max_points=100.0,
                weight=0.4,
                course_id=course1.id,
            )
            add_exam(
                name="Final 1",
                max_points=150.0,
                weight=0.6,
                course_id=course1.id,
            )

            # Add exam to course 2
            add_exam(
                name="Final 2",
                max_points=200.0,
                weight=1.0,
                course_id=course2.id,
            )

            return {"course1_id": course1.id, "course2_id": course2.id}

    def test_list_all_exams(self, app, db, sample_courses_with_exams):
        """Test listing all exams."""
        with app.app_context():
            exams = list_exams()
            assert len(exams) == 3

    def test_list_exams_by_course(self, app, db, sample_courses_with_exams):
        """Test filtering exams by course."""
        with app.app_context():
            course1_id = sample_courses_with_exams["course1_id"]
            course2_id = sample_courses_with_exams["course2_id"]

            exams1 = list_exams(course_id=course1_id)
            assert len(exams1) == 2
            assert all(e.course_id == course1_id for e in exams1)

            exams2 = list_exams(course_id=course2_id)
            assert len(exams2) == 1
            assert exams2[0].course_id == course2_id

    def test_list_exams_empty(self, app, db):
        """Test listing exams when none exist."""
        with app.app_context():
            exams = list_exams()
            assert len(exams) == 0


class TestGetExam:
    """Test get_exam function."""

    @pytest.fixture
    def sample_exam(self, app, db):
        """Create a sample exam for testing."""
        with app.app_context():
            university = add_university("Test University")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                name="Test Exam",
                max_points=100.0,
                weight=0.5,
                course_id=course.id,
            )
            return exam.id

    def test_get_exam_success(self, app, db, sample_exam):
        """Test getting an exam by ID."""
        with app.app_context():
            exam = get_exam(sample_exam)
            assert exam is not None
            assert exam.id == sample_exam
            assert exam.name == "Test Exam"

    def test_get_exam_not_found(self, app, db):
        """Test getting a nonexistent exam."""
        with app.app_context():
            exam = get_exam(99999)
            assert exam is None


class TestUpdateExam:
    """Test update_exam function."""

    @pytest.fixture
    def sample_exam(self, app, db):
        """Create a sample exam for testing."""
        with app.app_context():
            university = add_university("Test University")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                name="Original Exam",
                max_points=100.0,
                weight=0.5,
                course_id=course.id,
                description="Original description",
            )
            return exam.id

    def test_update_exam_name(self, app, db, sample_exam):
        """Test updating exam name."""
        with app.app_context():
            exam = update_exam(sample_exam, name="Updated Exam")
            assert exam is not None
            assert exam.name == "Updated Exam"
            assert exam.max_points == 100.0  # Unchanged

    def test_update_exam_max_points(self, app, db, sample_exam):
        """Test updating max points."""
        with app.app_context():
            exam = update_exam(sample_exam, max_points=150.0)
            assert exam is not None
            assert exam.max_points == 150.0
            assert exam.name == "Original Exam"  # Unchanged

    def test_update_exam_weight(self, app, db, sample_exam):
        """Test updating weight."""
        with app.app_context():
            exam = update_exam(sample_exam, weight=0.7)
            assert exam is not None
            assert exam.weight == 0.7

    def test_update_exam_description(self, app, db, sample_exam):
        """Test updating description."""
        with app.app_context():
            exam = update_exam(sample_exam, description="New description")
            assert exam is not None
            assert exam.description == "New description"

    def test_update_exam_dates(self, app, db, sample_exam):
        """Test updating dates."""
        with app.app_context():
            exam_date = date(2024, 3, 15)
            due_date = date(2024, 3, 20)

            exam = update_exam(
                sample_exam,
                exam_date=exam_date,
                due_date=due_date,
            )
            assert exam is not None
            assert exam.exam_date == exam_date
            assert exam.due_date == due_date

    def test_update_exam_multiple_fields(self, app, db, sample_exam):
        """Test updating multiple fields at once."""
        with app.app_context():
            exam = update_exam(
                sample_exam,
                name="Updated Name",
                max_points=200.0,
                weight=0.8,
            )
            assert exam is not None
            assert exam.name == "Updated Name"
            assert exam.max_points == 200.0
            assert exam.weight == 0.8

    def test_update_exam_not_found(self, app, db):
        """Test updating a nonexistent exam."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam with ID 99999 not found"):
                update_exam(99999, name="Updated")

    def test_update_exam_empty_name(self, app, db, sample_exam):
        """Test that updating to empty name fails."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam name cannot be empty"):
                update_exam(sample_exam, name="")

    def test_update_exam_invalid_max_points(self, app, db, sample_exam):
        """Test that updating to invalid max_points fails."""
        with app.app_context():
            with pytest.raises(ValueError, match="Max points must be positive"):
                update_exam(sample_exam, max_points=-10.0)

    def test_update_exam_invalid_weight(self, app, db, sample_exam):
        """Test that updating to invalid weight fails."""
        with app.app_context():
            with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
                update_exam(sample_exam, weight=1.5)

    def test_update_exam_date_after_due_date(self, app, db, sample_exam):
        """Test that exam_date after due_date fails."""
        with app.app_context():
            # First set due date
            update_exam(sample_exam, due_date=date(2024, 3, 15))

            # Then try to set exam_date after due_date
            with pytest.raises(ValueError, match="Exam date cannot be after due date"):
                update_exam(sample_exam, exam_date=date(2024, 3, 20))


class TestDeleteExam:
    """Test delete_exam function."""

    @pytest.fixture
    def sample_exam(self, app, db):
        """Create a sample exam for testing."""
        with app.app_context():
            university = add_university("Test University")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                name="Test Exam",
                max_points=100.0,
                weight=0.5,
                course_id=course.id,
            )
            return exam.id

    def test_delete_exam_success(self, app, db, sample_exam):
        """Test deleting an exam successfully."""
        with app.app_context():
            result = delete_exam(sample_exam)
            assert result is True

            # Verify exam is deleted
            exam = get_exam(sample_exam)
            assert exam is None

    def test_delete_exam_not_found(self, app, db):
        """Test deleting a nonexistent exam."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam with ID 99999 not found"):
                delete_exam(99999)
