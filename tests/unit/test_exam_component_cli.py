"""
Unit tests for exam component CLI tool.

This module tests all exam component management CLI functions.
"""

import pytest

from cli.exam_component_cli import (
    add_component,
    delete_component,
    get_component,
    list_components,
    update_component,
    validate_total_weight,
    get_available_weight,
)
from app.models.exam_component import (
    validate_weight,
    validate_max_points,
    validate_order,
)
from app.models.university import University
from app.models.course import Course
from app.models.exam import Exam
import app as app_module


class TestValidationFunctions:
    """Test validation helper functions."""

    def test_validate_weight_valid(self):
        """Test that valid weights pass validation."""
        assert validate_weight(0.0) is True
        assert validate_weight(0.4) is True
        assert validate_weight(0.6) is True
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

    def test_validate_order_valid(self):
        """Test that valid orders pass validation."""
        assert validate_order(0) is True
        assert validate_order(1) is True
        assert validate_order(10) is True

    def test_validate_order_invalid(self):
        """Test that invalid orders fail validation."""
        assert validate_order(-1) is False
        assert validate_order(-10) is False


class TestAddComponent:
    """Test add_component function."""

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

            exam = Exam(
                name="Test Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )
            app_module.db_session.add(exam)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]
            return exam.id

    def test_add_component_success(self, app, db, sample_exam):
        """Test adding a component successfully."""
        with app.app_context():
            component = add_component(
                name="Written Part",
                max_points=60.0,
                weight=0.6,
                exam_id=sample_exam,
            )

            assert component is not None
            assert component.id is not None
            assert component.name == "Written Part"
            assert component.max_points == 60.0
            assert component.weight == 0.6
            assert component.exam_id == sample_exam
            assert component.order == 0

    def test_add_component_with_description(self, app, db, sample_exam):
        """Test adding a component with description."""
        with app.app_context():
            component = add_component(
                name="Practical Part",
                max_points=40.0,
                weight=0.4,
                exam_id=sample_exam,
                description="Hands-on coding exercise",
            )

            assert component is not None
            assert component.description == "Hands-on coding exercise"

    def test_add_component_with_order(self, app, db, sample_exam):
        """Test adding a component with custom order."""
        with app.app_context():
            component = add_component(
                name="Part 1",
                max_points=50.0,
                weight=0.5,
                exam_id=sample_exam,
                order=1,
            )

            assert component is not None
            assert component.order == 1

    def test_add_component_empty_name(self, app, db, sample_exam):
        """Test that empty name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Component name cannot be empty"):
                add_component(
                    name="",
                    max_points=60.0,
                    weight=0.6,
                    exam_id=sample_exam,
                )

    def test_add_component_whitespace_name(self, app, db, sample_exam):
        """Test that whitespace-only name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Component name cannot be empty"):
                add_component(
                    name="   ",
                    max_points=60.0,
                    weight=0.6,
                    exam_id=sample_exam,
                )

    def test_add_component_name_too_long(self, app, db, sample_exam):
        """Test that name exceeding 255 characters raises ValueError."""
        with app.app_context():
            long_name = "A" * 256
            with pytest.raises(ValueError, match="cannot exceed 255 characters"):
                add_component(
                    name=long_name,
                    max_points=60.0,
                    weight=0.6,
                    exam_id=sample_exam,
                )

    def test_add_component_invalid_max_points_zero(self, app, db, sample_exam):
        """Test that zero max_points raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid max_points"):
                add_component(
                    name="Test Component",
                    max_points=0.0,
                    weight=0.6,
                    exam_id=sample_exam,
                )

    def test_add_component_invalid_max_points_negative(self, app, db, sample_exam):
        """Test that negative max_points raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid max_points"):
                add_component(
                    name="Test Component",
                    max_points=-10.0,
                    weight=0.6,
                    exam_id=sample_exam,
                )

    def test_add_component_invalid_weight_negative(self, app, db, sample_exam):
        """Test that negative weight raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid weight"):
                add_component(
                    name="Test Component",
                    max_points=60.0,
                    weight=-0.1,
                    exam_id=sample_exam,
                )

    def test_add_component_invalid_weight_too_large(self, app, db, sample_exam):
        """Test that weight > 1 raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid weight"):
                add_component(
                    name="Test Component",
                    max_points=60.0,
                    weight=1.5,
                    exam_id=sample_exam,
                )

    def test_add_component_invalid_order(self, app, db, sample_exam):
        """Test that negative order raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid order"):
                add_component(
                    name="Test Component",
                    max_points=60.0,
                    weight=0.6,
                    exam_id=sample_exam,
                    order=-1,
                )

    def test_add_component_invalid_exam_id(self, app, db):
        """Test that invalid exam_id raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Exam with ID 9999 not found"):
                add_component(
                    name="Test Component",
                    max_points=60.0,
                    weight=0.6,
                    exam_id=9999,
                )

    def test_add_component_weight_exceeds_total(self, app, db, sample_exam):
        """Test that weight exceeding 1.0 total raises ValueError."""
        with app.app_context():
            # Add first component with weight 0.7
            add_component(
                name="Part 1",
                max_points=70.0,
                weight=0.7,
                exam_id=sample_exam,
            )

            # Try to add second component with weight 0.5 (total would be 1.2)
            with pytest.raises(ValueError, match="Only 0.300 weight available"):
                add_component(
                    name="Part 2",
                    max_points=50.0,
                    weight=0.5,
                    exam_id=sample_exam,
                )

    def test_add_components_totaling_one(self, app, db, sample_exam):
        """Test adding multiple components that sum to 1.0."""
        with app.app_context():
            # Add components that total 1.0
            add_component(
                name="Part 1",
                max_points=60.0,
                weight=0.6,
                exam_id=sample_exam,
            )

            add_component(
                name="Part 2",
                max_points=40.0,
                weight=0.4,
                exam_id=sample_exam,
            )

            # Verify total weight
            is_valid, total = validate_total_weight(sample_exam)
            assert is_valid is True
            assert abs(total - 1.0) < 0.001


class TestListComponents:
    """Test list_components function."""

    @pytest.fixture
    def sample_components(self, app, db):
        """Create sample components for testing."""
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

            exam1 = Exam(
                name="Exam 1",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )
            exam2 = Exam(
                name="Exam 2",
                exam_type="final",
                max_points=150.0,
                weight=0.5,
                course_id=course.id,
            )
            app_module.db_session.add(exam1)  # type: ignore[union-attr]
            app_module.db_session.add(exam2)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            # Add components using the CLI function
            add_component("Written Part", 60.0, 0.6, exam1.id, order=0)
            add_component("Practical Part", 40.0, 0.4, exam1.id, order=1)
            add_component("Theory Part", 75.0, 0.5, exam2.id, order=0)
            add_component("Lab Part", 75.0, 0.5, exam2.id, order=1)

            return {"exam1_id": exam1.id, "exam2_id": exam2.id}

    def test_list_components_all(self, app, db, sample_components):
        """Test listing all components."""
        with app.app_context():
            components = list_components()
            assert len(components) == 4

    def test_list_components_filter_by_exam(self, app, db, sample_components):
        """Test filtering components by exam."""
        with app.app_context():
            components = list_components(exam_id=sample_components["exam1_id"])
            assert len(components) == 2
            assert all(c.exam_id == sample_components["exam1_id"] for c in components)

    def test_list_components_empty_result(self, app, db, sample_components):
        """Test that empty list is returned when no components match."""
        with app.app_context():
            components = list_components(exam_id=9999)
            assert components == []

    def test_list_components_ordering(self, app, db, sample_components):
        """Test that components are ordered by exam_id and order."""
        with app.app_context():
            components = list_components(exam_id=sample_components["exam1_id"])
            assert components[0].name == "Written Part"
            assert components[0].order == 0
            assert components[1].name == "Practical Part"
            assert components[1].order == 1


class TestGetComponent:
    """Test get_component function."""

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

            exam = Exam(
                name="Test Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )
            app_module.db_session.add(exam)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            component = add_component("Written Part", 60.0, 0.6, exam.id)
            return component.id  # type: ignore[union-attr]

    def test_get_component_success(self, app, db, sample_component):
        """Test getting a component successfully."""
        with app.app_context():
            component = get_component(sample_component)

            assert component is not None
            assert component.id == sample_component
            assert component.name == "Written Part"

    def test_get_component_not_found(self, app, db):
        """Test getting non-existent component returns None."""
        with app.app_context():
            component = get_component(9999)
            assert component is None


class TestUpdateComponent:
    """Test update_component function."""

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

            exam = Exam(
                name="Test Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )
            app_module.db_session.add(exam)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            component = add_component("Written Part", 60.0, 0.6, exam.id)
            return component.id  # type: ignore[union-attr]

    def test_update_component_name(self, app, db, sample_component):
        """Test updating component name."""
        with app.app_context():
            component = update_component(sample_component, name="Updated Part")

            assert component is not None
            assert component.name == "Updated Part"

    def test_update_component_max_points(self, app, db, sample_component):
        """Test updating max_points."""
        with app.app_context():
            component = update_component(sample_component, max_points=70.0)

            assert component is not None
            assert component.max_points == 70.0

    def test_update_component_weight(self, app, db, sample_component):
        """Test updating weight."""
        with app.app_context():
            component = update_component(sample_component, weight=0.7)

            assert component is not None
            assert component.weight == 0.7

    def test_update_component_description(self, app, db, sample_component):
        """Test updating description."""
        with app.app_context():
            component = update_component(
                sample_component, description="Updated description"
            )

            assert component is not None
            assert component.description == "Updated description"

    def test_update_component_order(self, app, db, sample_component):
        """Test updating order."""
        with app.app_context():
            component = update_component(sample_component, order=2)

            assert component is not None
            assert component.order == 2

    def test_update_component_not_found(self, app, db):
        """Test updating non-existent component raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Component with ID 9999 not found"):
                update_component(9999, name="Updated Name")

    def test_update_component_invalid_name_empty(self, app, db, sample_component):
        """Test updating with empty name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Component name cannot be empty"):
                update_component(sample_component, name="   ")

    def test_update_component_invalid_max_points(self, app, db, sample_component):
        """Test updating with invalid max_points raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid max_points"):
                update_component(sample_component, max_points=0.0)

    def test_update_component_invalid_weight(self, app, db, sample_component):
        """Test updating with invalid weight raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid weight"):
                update_component(sample_component, weight=1.5)

    def test_update_component_weight_exceeds_total(self, app, db, sample_component):
        """Test updating weight that would exceed 1.0 total raises ValueError."""
        with app.app_context():
            # Get the component's exam_id
            component = get_component(sample_component)
            exam_id = component.exam_id  # type: ignore[union-attr]

            # Add another component
            add_component("Practical Part", 40.0, 0.3, exam_id)

            # Try to update first component to weight that exceeds total
            # Available: 1.0 - 0.3 = 0.7, trying to set 0.8 should fail
            with pytest.raises(ValueError, match="Only 0.700 weight available"):
                update_component(sample_component, weight=0.8)

    def test_update_component_multiple_fields(self, app, db, sample_component):
        """Test updating multiple fields at once."""
        with app.app_context():
            component = update_component(
                sample_component,
                name="Updated Part",
                max_points=70.0,
                weight=0.7,
                order=1,
            )

            assert component is not None
            assert component.name == "Updated Part"
            assert component.max_points == 70.0
            assert component.weight == 0.7
            assert component.order == 1


class TestDeleteComponent:
    """Test delete_component function."""

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

            exam = Exam(
                name="Test Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )
            app_module.db_session.add(exam)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]

            component = add_component("Written Part", 60.0, 0.6, exam.id)
            return component.id  # type: ignore[union-attr]

    def test_delete_component_success(self, app, db, sample_component):
        """Test deleting a component successfully."""
        with app.app_context():
            result = delete_component(sample_component)
            assert result is True

            # Verify component is deleted
            component = get_component(sample_component)
            assert component is None

    def test_delete_component_not_found(self, app, db):
        """Test deleting non-existent component raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Component with ID 9999 not found"):
                delete_component(9999)


class TestWeightValidation:
    """Test weight validation functions."""

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

            exam = Exam(
                name="Test Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )
            app_module.db_session.add(exam)  # type: ignore[union-attr]
            app_module.db_session.commit()  # type: ignore[union-attr]
            return exam.id

    def test_validate_total_weight_empty(self, app, db, sample_exam):
        """Test total weight validation with no components."""
        with app.app_context():
            is_valid, total = validate_total_weight(sample_exam)
            assert is_valid is False
            assert total == 0.0

    def test_validate_total_weight_valid(self, app, db, sample_exam):
        """Test total weight validation with components summing to 1.0."""
        with app.app_context():
            add_component("Part 1", 60.0, 0.6, sample_exam)
            add_component("Part 2", 40.0, 0.4, sample_exam)

            is_valid, total = validate_total_weight(sample_exam)
            assert is_valid is True
            assert abs(total - 1.0) < 0.001

    def test_validate_total_weight_invalid_too_low(self, app, db, sample_exam):
        """Test total weight validation with components summing < 1.0."""
        with app.app_context():
            add_component("Part 1", 50.0, 0.5, sample_exam)

            is_valid, total = validate_total_weight(sample_exam)
            assert is_valid is False
            assert total == 0.5

    def test_get_available_weight_empty(self, app, db, sample_exam):
        """Test available weight with no components."""
        with app.app_context():
            available = get_available_weight(sample_exam)
            assert available == 1.0

    def test_get_available_weight_partial(self, app, db, sample_exam):
        """Test available weight with some components."""
        with app.app_context():
            add_component("Part 1", 60.0, 0.6, sample_exam)

            available = get_available_weight(sample_exam)
            assert abs(available - 0.4) < 0.001

    def test_get_available_weight_exclude_component(self, app, db, sample_exam):
        """Test available weight excluding a specific component."""
        with app.app_context():
            comp1 = add_component("Part 1", 60.0, 0.6, sample_exam)
            add_component("Part 2", 40.0, 0.4, sample_exam)

            # Get available weight excluding comp1 (comp2 uses 0.4, so 0.6 available)
            available = get_available_weight(sample_exam, comp1.id)  # type: ignore[arg-type]
            assert abs(available - 0.6) < 0.001
