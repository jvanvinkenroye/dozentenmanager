"""
Unit tests for exam CLI tool.

This module tests all exam and exam component management CLI functions.
"""

from datetime import date, timedelta
import pytest

from cli.exam_cli import (
    add_exam,
    add_exam_component,
    delete_exam,
    delete_exam_component,
    list_exam_components,
    list_exams,
    show_exam,
    update_exam,
    update_exam_component,
    validate_exam_component_weights,
)
from app.models.exam import validate_weight, validate_max_points, validate_due_date
from app.models.course import Course
from app.models.university import University
import app as app_module


class TestValidationFunctions:
    """Test validation helper functions."""

    def test_validate_weight_valid(self):
        """Test that valid weight values pass validation."""
        assert validate_weight(0.0) is True
        assert validate_weight(0.5) is True
        assert validate_weight(0.6) is True
        assert validate_weight(1.0) is True

    def test_validate_weight_invalid(self):
        """Test that invalid weight values fail validation."""
        assert validate_weight(-0.1) is False
        assert validate_weight(1.5) is False
        assert validate_weight(-1.0) is False
        assert validate_weight(2.0) is False

    def test_validate_max_points_valid(self):
        """Test that valid max_points values pass validation."""
        assert validate_max_points(0.1) is True
        assert validate_max_points(50.0) is True
        assert validate_max_points(100.0) is True
        assert validate_max_points(120.5) is True

    def test_validate_max_points_invalid(self):
        """Test that invalid max_points values fail validation."""
        assert validate_max_points(0.0) is False
        assert validate_max_points(-10.0) is False
        assert validate_max_points(-0.1) is False

    def test_validate_due_date_future(self):
        """Test that future dates pass validation."""
        future_date = date.today() + timedelta(days=30)
        assert validate_due_date(future_date) is True
        assert validate_due_date(future_date, allow_past=True) is True

    def test_validate_due_date_today(self):
        """Test that today's date passes validation."""
        today = date.today()
        assert validate_due_date(today) is True
        assert validate_due_date(today, allow_past=True) is True

    def test_validate_due_date_past(self):
        """Test that past dates fail validation without allow_past."""
        past_date = date.today() - timedelta(days=30)
        assert validate_due_date(past_date) is False
        assert validate_due_date(past_date, allow_past=True) is True


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
            return course.id

    def test_add_exam_success(self, app, db, sample_course):
        """Test adding an exam successfully."""
        with app.app_context():
            exam = add_exam(
                course_id=sample_course,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )

            assert exam is not None
            assert exam.id is not None
            assert exam.name == "Final Exam"
            assert exam.max_points == 100.0
            assert exam.weight == 0.6
            assert exam.course_id == sample_course
            assert exam.due_date is None

    def test_add_exam_with_due_date(self, app, db, sample_course):
        """Test adding an exam with a due date."""
        with app.app_context():
            future_date = (date.today() + timedelta(days=30)).isoformat()
            exam = add_exam(
                course_id=sample_course,
                name="Midterm Exam",
                max_points=80.0,
                weight=0.4,
                due_date=future_date,
            )

            assert exam is not None
            assert exam.due_date is not None
            assert exam.due_date.isoformat() == future_date

    def test_add_exam_empty_name(self, app, db, sample_course):
        """Test that adding an exam with empty name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam name cannot be empty"):
                add_exam(
                    course_id=sample_course,
                    name="",
                    max_points=100.0,
                    weight=0.6,
                )

    def test_add_exam_invalid_max_points(self, app, db, sample_course):
        """Test that invalid max_points raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Max points must be positive"):
                add_exam(
                    course_id=sample_course,
                    name="Final Exam",
                    max_points=0.0,
                    weight=0.6,
                )

            with pytest.raises(ValueError, match="Max points must be positive"):
                add_exam(
                    course_id=sample_course,
                    name="Final Exam",
                    max_points=-10.0,
                    weight=0.6,
                )

    def test_add_exam_invalid_weight(self, app, db, sample_course):
        """Test that invalid weight raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Weight must be between 0 and 1"):
                add_exam(
                    course_id=sample_course,
                    name="Final Exam",
                    max_points=100.0,
                    weight=1.5,
                )

            with pytest.raises(ValueError, match="Weight must be between 0 and 1"):
                add_exam(
                    course_id=sample_course,
                    name="Final Exam",
                    max_points=100.0,
                    weight=-0.1,
                )

    def test_add_exam_invalid_course(self, app, db):
        """Test that adding an exam with invalid course_id raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Course with ID 99999 not found"):
                add_exam(
                    course_id=99999,
                    name="Final Exam",
                    max_points=100.0,
                    weight=0.6,
                )

    def test_add_exam_past_due_date(self, app, db, sample_course):
        """Test that adding an exam with past due date raises ValueError."""
        with app.app_context():
            past_date = (date.today() - timedelta(days=30)).isoformat()
            with pytest.raises(ValueError, match="Due date cannot be in the past"):
                add_exam(
                    course_id=sample_course,
                    name="Final Exam",
                    max_points=100.0,
                    weight=0.6,
                    due_date=past_date,
                )


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
                name="Test Course 1",
                slug="test-course-1",
                semester="2023_SoSe",
                university_id=university.id,
            )
            course2 = Course(
                name="Test Course 2",
                slug="test-course-2",
                semester="2023_SoSe",
                university_id=university.id,
            )
            app_module.db_session.add_all([course1, course2])  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            # Add exams to courses
            add_exam(course1.id, "Final Exam", 100.0, 0.6)
            add_exam(course1.id, "Midterm Exam", 80.0, 0.4)
            add_exam(course2.id, "Final Exam", 120.0, 1.0)

            return {"course1_id": course1.id, "course2_id": course2.id}

    def test_list_all_exams(self, app, db, sample_exams):
        """Test listing all exams."""
        with app.app_context():
            exams = list_exams()
            assert len(exams) == 3

    def test_list_exams_by_course(self, app, db, sample_exams):
        """Test listing exams filtered by course."""
        with app.app_context():
            exams = list_exams(course_id=sample_exams["course1_id"])
            assert len(exams) == 2

            exams = list_exams(course_id=sample_exams["course2_id"])
            assert len(exams) == 1


class TestShowExam:
    """Test show_exam function."""

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

            exam = add_exam(course.id, "Final Exam", 100.0, 0.6)
            return exam.id

    def test_show_exam_success(self, app, db, sample_exam):
        """Test showing an exam successfully."""
        with app.app_context():
            exam = show_exam(sample_exam)
            assert exam is not None
            assert exam.id == sample_exam
            assert exam.name == "Final Exam"

    def test_show_exam_not_found(self, app, db):
        """Test showing a non-existent exam returns None."""
        with app.app_context():
            exam = show_exam(99999)
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

            exam = add_exam(course.id, "Final Exam", 100.0, 0.6)
            return exam.id

    def test_update_exam_name(self, app, db, sample_exam):
        """Test updating exam name."""
        with app.app_context():
            exam = update_exam(sample_exam, name="Updated Final Exam")
            assert exam is not None
            assert exam.name == "Updated Final Exam"

    def test_update_exam_max_points(self, app, db, sample_exam):
        """Test updating exam max points."""
        with app.app_context():
            exam = update_exam(sample_exam, max_points=120.0)
            assert exam is not None
            assert exam.max_points == 120.0

    def test_update_exam_weight(self, app, db, sample_exam):
        """Test updating exam weight."""
        with app.app_context():
            exam = update_exam(sample_exam, weight=0.7)
            assert exam is not None
            assert exam.weight == 0.7

    def test_update_exam_not_found(self, app, db):
        """Test updating a non-existent exam raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam with ID 99999 not found"):
                update_exam(99999, name="Updated Name")


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

            exam = add_exam(course.id, "Final Exam", 100.0, 0.6)
            return exam.id

    def test_delete_exam_success(self, app, db, sample_exam):
        """Test deleting an exam successfully."""
        with app.app_context():
            result = delete_exam(sample_exam)
            assert result is True

            # Verify exam was deleted
            exam = show_exam(sample_exam)
            assert exam is None

    def test_delete_exam_not_found(self, app, db):
        """Test deleting a non-existent exam raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam with ID 99999 not found"):
                delete_exam(99999)


class TestAddExamComponent:
    """Test add_exam_component function."""

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

            exam = add_exam(course.id, "Final Exam", 100.0, 0.6)
            return exam.id

    def test_add_component_success(self, app, db, sample_exam):
        """Test adding a component successfully."""
        with app.app_context():
            component = add_exam_component(
                exam_id=sample_exam,
                name="Multiple Choice",
                max_points=40.0,
                weight=0.4,
                order=1,
            )

            assert component is not None
            assert component.id is not None
            assert component.name == "Multiple Choice"
            assert component.max_points == 40.0
            assert component.weight == 0.4
            assert component.order == 1
            assert component.exam_id == sample_exam

    def test_add_component_empty_name(self, app, db, sample_exam):
        """Test that adding a component with empty name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Component name cannot be empty"):
                add_exam_component(
                    exam_id=sample_exam,
                    name="",
                    max_points=40.0,
                    weight=0.4,
                )

    def test_add_component_invalid_max_points(self, app, db, sample_exam):
        """Test that invalid max_points raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Max points must be positive"):
                add_exam_component(
                    exam_id=sample_exam,
                    name="Multiple Choice",
                    max_points=0.0,
                    weight=0.4,
                )

    def test_add_component_invalid_weight(self, app, db, sample_exam):
        """Test that invalid weight raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Weight must be between 0 and 1"):
                add_exam_component(
                    exam_id=sample_exam,
                    name="Multiple Choice",
                    max_points=40.0,
                    weight=1.5,
                )

    def test_add_component_duplicate_order(self, app, db, sample_exam):
        """Test that duplicate order raises IntegrityError."""
        with app.app_context():
            # Add first component
            add_exam_component(
                exam_id=sample_exam,
                name="Multiple Choice",
                max_points=40.0,
                weight=0.4,
                order=1,
            )

            # Try to add second component with same order
            from sqlalchemy.exc import IntegrityError

            with pytest.raises(IntegrityError, match="UNIQUE constraint|already exists"):
                add_exam_component(
                    exam_id=sample_exam,
                    name="Essay Questions",
                    max_points=60.0,
                    weight=0.6,
                    order=1,
                )


class TestListExamComponents:
    """Test list_exam_components function."""

    @pytest.fixture
    def sample_exam_with_components(self, app, db):
        """Create a sample exam with components for testing."""
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

            exam = add_exam(course.id, "Final Exam", 100.0, 0.6)

            # Add components
            add_exam_component(exam.id, "Multiple Choice", 40.0, 0.4, order=1)
            add_exam_component(exam.id, "Essay Questions", 60.0, 0.6, order=2)

            return exam.id

    def test_list_components(self, app, db, sample_exam_with_components):
        """Test listing exam components."""
        with app.app_context():
            components = list_exam_components(sample_exam_with_components)
            assert len(components) == 2
            # Check ordering
            assert components[0].order == 1
            assert components[1].order == 2


class TestUpdateExamComponent:
    """Test update_exam_component function."""

    @pytest.fixture
    def sample_component(self, app, db):
        """Create a sample component for testing."""
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

            exam = add_exam(course.id, "Final Exam", 100.0, 0.6)
            component = add_exam_component(exam.id, "Multiple Choice", 40.0, 0.4)
            return component.id

    def test_update_component_name(self, app, db, sample_component):
        """Test updating component name."""
        with app.app_context():
            component = update_exam_component(
                sample_component, name="Updated Multiple Choice"
            )
            assert component is not None
            assert component.name == "Updated Multiple Choice"

    def test_update_component_max_points(self, app, db, sample_component):
        """Test updating component max points."""
        with app.app_context():
            component = update_exam_component(sample_component, max_points=50.0)
            assert component is not None
            assert component.max_points == 50.0


class TestDeleteExamComponent:
    """Test delete_exam_component function."""

    @pytest.fixture
    def sample_component(self, app, db):
        """Create a sample component for testing."""
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

            exam = add_exam(course.id, "Final Exam", 100.0, 0.6)
            component = add_exam_component(exam.id, "Multiple Choice", 40.0, 0.4)
            return component.id

    def test_delete_component_success(self, app, db, sample_component):
        """Test deleting a component successfully."""
        with app.app_context():
            result = delete_exam_component(sample_component)
            assert result is True


class TestValidateComponentWeights:
    """Test validate_exam_component_weights function."""

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

            exam = add_exam(course.id, "Final Exam", 100.0, 0.6)
            return exam.id

    def test_validate_weights_sum_to_one(self, app, db, sample_exam):
        """Test that weights summing to 1.0 are valid."""
        with app.app_context():
            # Add components that sum to 1.0
            add_exam_component(sample_exam, "Part 1", 40.0, 0.4, order=1)
            add_exam_component(sample_exam, "Part 2", 60.0, 0.6, order=2)

            is_valid, total_weight = validate_exam_component_weights(sample_exam)
            assert is_valid is True
            assert abs(total_weight - 1.0) < 0.01

    def test_validate_weights_not_sum_to_one(self, app, db, sample_exam):
        """Test that weights not summing to 1.0 are invalid."""
        with app.app_context():
            # Add components that don't sum to 1.0
            add_exam_component(sample_exam, "Part 1", 40.0, 0.3, order=1)
            add_exam_component(sample_exam, "Part 2", 60.0, 0.5, order=2)

            is_valid, total_weight = validate_exam_component_weights(sample_exam)
            assert is_valid is False
            assert abs(total_weight - 0.8) < 0.01
