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
from app.models.exam import validate_max_points, validate_weight, validate_exam_date
from app.models.university import University
from app.models.course import Course
import app as app_module


class TestValidationFunctions:
    """Test validation helper functions."""

    def test_validate_max_points_valid(self):
        """Test that valid max points pass validation."""
        assert validate_max_points(100.0) is True
        assert validate_max_points(50.5) is True
        assert validate_max_points(0.1) is True
        assert validate_max_points(1000.0) is True

    def test_validate_max_points_invalid(self):
        """Test that invalid max points fail validation."""
        assert validate_max_points(0.0) is False
        assert validate_max_points(-10.0) is False
        assert validate_max_points(-0.1) is False

    def test_validate_weight_valid(self):
        """Test that valid weights pass validation."""
        assert validate_weight(100.0) is True
        assert validate_weight(50.0) is True
        assert validate_weight(0.0) is True
        assert validate_weight(33.33) is True

    def test_validate_weight_invalid(self):
        """Test that invalid weights fail validation."""
        assert validate_weight(101.0) is False
        assert validate_weight(150.0) is False
        assert validate_weight(-1.0) is False
        assert validate_weight(-10.0) is False

    def test_validate_exam_date_valid(self):
        """Test that valid dates pass validation."""
        assert validate_exam_date(date.today()) is True
        assert validate_exam_date(date(2024, 6, 15)) is True
        assert validate_exam_date(date(2025, 12, 31)) is True

    def test_validate_exam_date_invalid(self):
        """Test that None fails validation."""
        assert validate_exam_date(None) is False  # type: ignore[arg-type]


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
                name="Introduction to Statistics",
                slug="intro-statistics",
                semester="2024_SoSe",
                university_id=university.id,
            )
            app_module.db_session.add(course)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]
            # Return the ID to avoid detached instance issues
            return course.id

    def test_add_exam_success(self, app, db, sample_course):
        """Test adding an exam successfully."""
        with app.app_context():
            exam_date = date(2024, 6, 15)
            exam = add_exam(
                name="Klausur Statistik I",
                course_id=sample_course,
                exam_date=exam_date,
                max_points=100.0,
                weight=100.0,
            )

            assert exam is not None
            assert exam.id is not None
            assert exam.name == "Klausur Statistik I"
            assert exam.course_id == sample_course
            assert exam.exam_date == exam_date
            assert exam.max_points == 100.0
            assert exam.weight == 100.0
            assert exam.description is None

    def test_add_exam_with_description(self, app, db, sample_course):
        """Test adding an exam with description."""
        with app.app_context():
            exam = add_exam(
                name="Klausur Statistik I",
                course_id=sample_course,
                exam_date=date(2024, 6, 15),
                max_points=100.0,
                weight=100.0,
                description="Written exam with multiple choice and open questions",
            )

            assert (
                exam.description
                == "Written exam with multiple choice and open questions"
            )

    def test_add_exam_with_partial_weight(self, app, db, sample_course):
        """Test adding an exam with partial weight."""
        with app.app_context():
            exam = add_exam(
                name="Midterm Exam",
                course_id=sample_course,
                exam_date=date(2024, 5, 1),
                max_points=50.0,
                weight=40.0,
            )

            assert exam.weight == 40.0

    def test_add_exam_strips_whitespace(self, app, db, sample_course):
        """Test that whitespace is stripped from fields."""
        with app.app_context():
            exam = add_exam(
                name="  Klausur Statistik I  ",
                course_id=sample_course,
                exam_date=date(2024, 6, 15),
                max_points=100.0,
                description="  Test description  ",
            )

            assert exam.name == "Klausur Statistik I"
            assert exam.description == "Test description"

    def test_add_exam_empty_name(self, app, db, sample_course):
        """Test that empty name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam name cannot be empty"):
                add_exam(
                    name="",
                    course_id=sample_course,
                    exam_date=date(2024, 6, 15),
                    max_points=100.0,
                )

    def test_add_exam_name_too_long(self, app, db, sample_course):
        """Test that name exceeding 255 characters raises ValueError."""
        with app.app_context():
            long_name = "A" * 256
            with pytest.raises(
                ValueError, match="Exam name cannot exceed 255 characters"
            ):
                add_exam(
                    name=long_name,
                    course_id=sample_course,
                    exam_date=date(2024, 6, 15),
                    max_points=100.0,
                )

    def test_add_exam_invalid_course(self, app, db):
        """Test that non-existent course raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Course with ID 999 not found"):
                add_exam(
                    name="Klausur",
                    course_id=999,
                    exam_date=date(2024, 6, 15),
                    max_points=100.0,
                )

    def test_add_exam_invalid_max_points(self, app, db, sample_course):
        """Test that invalid max points raises ValueError."""
        with app.app_context():
            with pytest.raises(
                ValueError, match="Maximum points must be greater than 0"
            ):
                add_exam(
                    name="Klausur",
                    course_id=sample_course,
                    exam_date=date(2024, 6, 15),
                    max_points=0.0,
                )

    def test_add_exam_invalid_weight(self, app, db, sample_course):
        """Test that invalid weight raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Weight must be between 0 and 100"):
                add_exam(
                    name="Klausur",
                    course_id=sample_course,
                    exam_date=date(2024, 6, 15),
                    max_points=100.0,
                    weight=150.0,
                )

    def test_add_exam_description_too_long(self, app, db, sample_course):
        """Test that description exceeding 500 characters raises ValueError."""
        with app.app_context():
            long_description = "A" * 501
            with pytest.raises(
                ValueError, match="Description cannot exceed 500 characters"
            ):
                add_exam(
                    name="Klausur",
                    course_id=sample_course,
                    exam_date=date(2024, 6, 15),
                    max_points=100.0,
                    description=long_description,
                )


class TestListExams:
    """Test list_exams function."""

    @pytest.fixture
    def sample_exams(self, app, db):
        """Create sample exams for testing."""
        with app.app_context():
            # Create university and courses
            university = University(name="Test University", slug="test-university")
            app_module.db_session.add(university)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            course1 = Course(
                name="Statistics I",
                slug="statistics-i",
                semester="2024_SoSe",
                university_id=university.id,
            )
            course2 = Course(
                name="Data Science",
                slug="data-science",
                semester="2024_SoSe",
                university_id=university.id,
            )
            app_module.db_session.add_all([course1, course2])  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            # Store IDs
            course1_id = course1.id
            course2_id = course2.id

            # Create exams
            add_exam("Midterm", course1_id, date(2024, 5, 1), 50.0, 40.0)
            add_exam("Final Exam", course1_id, date(2024, 7, 15), 100.0, 60.0)
            add_exam("Klausur", course2_id, date(2024, 6, 20), 100.0, 100.0)

            return {"course1": course1_id, "course2": course2_id}

    def test_list_all_exams(self, app, db, sample_exams):
        """Test listing all exams."""
        with app.app_context():
            exams = list_exams()
            assert len(exams) == 3

    def test_list_exams_filter_by_course(self, app, db, sample_exams):
        """Test filtering exams by course."""
        with app.app_context():
            course1_exams = list_exams(course_id=sample_exams["course1"])
            assert len(course1_exams) == 2

            course2_exams = list_exams(course_id=sample_exams["course2"])
            assert len(course2_exams) == 1

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
            university = University(name="Test University", slug="test-university")
            app_module.db_session.add(university)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            course = Course(
                name="Statistics",
                slug="statistics",
                semester="2024_SoSe",
                university_id=university.id,
            )
            app_module.db_session.add(course)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            exam = add_exam("Klausur", course.id, date(2024, 6, 15), 100.0)
            return exam.id

    def test_get_exam_success(self, app, db, sample_exam):
        """Test getting an exam by ID."""
        with app.app_context():
            exam = get_exam(sample_exam)
            assert exam is not None
            assert exam.id == sample_exam
            assert exam.name == "Klausur"

    def test_get_exam_not_found(self, app, db):
        """Test getting non-existent exam returns None."""
        with app.app_context():
            exam = get_exam(999)
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
                name="Statistics",
                slug="statistics",
                semester="2024_SoSe",
                university_id=university.id,
            )
            app_module.db_session.add(course)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            exam = add_exam("Klausur", course.id, date(2024, 6, 15), 100.0)
            return exam.id

    def test_update_exam_name(self, app, db, sample_exam):
        """Test updating exam name."""
        with app.app_context():
            exam = update_exam(sample_exam, name="Final Exam")
            assert exam is not None
            assert exam.name == "Final Exam"

    def test_update_exam_date(self, app, db, sample_exam):
        """Test updating exam date."""
        with app.app_context():
            new_date = date(2024, 7, 1)
            exam = update_exam(sample_exam, exam_date=new_date)
            assert exam.exam_date == new_date

    def test_update_exam_max_points(self, app, db, sample_exam):
        """Test updating max points."""
        with app.app_context():
            exam = update_exam(sample_exam, max_points=120.0)
            assert exam.max_points == 120.0

    def test_update_exam_weight(self, app, db, sample_exam):
        """Test updating weight."""
        with app.app_context():
            exam = update_exam(sample_exam, weight=50.0)
            assert exam.weight == 50.0

    def test_update_exam_description(self, app, db, sample_exam):
        """Test updating description."""
        with app.app_context():
            exam = update_exam(sample_exam, description="Updated description")
            assert exam.description == "Updated description"

    def test_update_exam_multiple_fields(self, app, db, sample_exam):
        """Test updating multiple fields at once."""
        with app.app_context():
            new_date = date(2024, 7, 15)
            exam = update_exam(
                sample_exam,
                name="Updated Exam",
                exam_date=new_date,
                max_points=150.0,
                weight=75.0,
            )
            assert exam.name == "Updated Exam"
            assert exam.exam_date == new_date
            assert exam.max_points == 150.0
            assert exam.weight == 75.0

    def test_update_exam_not_found(self, app, db):
        """Test updating non-existent exam raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam with ID 999 not found"):
                update_exam(999, name="New Name")

    def test_update_exam_empty_name(self, app, db, sample_exam):
        """Test that empty name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam name cannot be empty"):
                update_exam(sample_exam, name="")

    def test_update_exam_invalid_max_points(self, app, db, sample_exam):
        """Test that invalid max points raises ValueError."""
        with app.app_context():
            with pytest.raises(
                ValueError, match="Maximum points must be greater than 0"
            ):
                update_exam(sample_exam, max_points=0.0)

    def test_update_exam_invalid_weight(self, app, db, sample_exam):
        """Test that invalid weight raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Weight must be between 0 and 100"):
                update_exam(sample_exam, weight=150.0)


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
                name="Statistics",
                slug="statistics",
                semester="2024_SoSe",
                university_id=university.id,
            )
            app_module.db_session.add(course)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            exam = add_exam("Klausur", course.id, date(2024, 6, 15), 100.0)
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
        """Test deleting non-existent exam raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam with ID 999 not found"):
                delete_exam(999)
