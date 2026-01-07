"""
Unit tests for course CLI tool.

This module tests all course management CLI functions.
"""

import pytest

from app.models.course import generate_slug, validate_semester
from app.models.university import University
from cli.course_cli import (
    add_course,
    delete_course,
    get_course,
    list_courses,
    update_course,
)


class TestValidationFunctions:
    """Test validation helper functions."""

    def test_validate_semester_valid_summer(self):
        """Test that valid summer semester formats pass validation."""
        assert validate_semester("2023_SoSe") is True
        assert validate_semester("2024_SoSe") is True
        assert validate_semester("1999_SoSe") is True

    def test_validate_semester_valid_winter(self):
        """Test that valid winter semester formats pass validation."""
        assert validate_semester("2023_WiSe") is True
        assert validate_semester("2024_WiSe") is True
        assert validate_semester("2000_WiSe") is True

    def test_validate_semester_invalid(self):
        """Test that invalid semester formats fail validation."""
        assert validate_semester("2023") is False  # Missing semester type
        assert validate_semester("2023_SS") is False  # Wrong abbreviation
        assert validate_semester("2023_WS") is False  # Wrong abbreviation
        assert validate_semester("23_SoSe") is False  # Year too short
        assert validate_semester("SoSe_2023") is False  # Wrong order
        assert validate_semester("2023-SoSe") is False  # Wrong separator
        assert validate_semester("") is False  # Empty

    def test_generate_slug_basic(self):
        """Test basic slug generation."""
        assert (
            generate_slug("Introduction to Statistics") == "introduction-to-statistics"
        )
        assert generate_slug("Data Science I") == "data-science-i"

    def test_generate_slug_umlauts(self):
        """Test slug generation with German umlauts."""
        assert generate_slug("Einführung Statistik") == "einfuehrung-statistik"
        assert generate_slug("Datenbanken für Anfänger") == "datenbanken-fuer-anfaenger"
        assert generate_slug("Übung Mathe") == "uebung-mathe"

    def test_generate_slug_special_characters(self):
        """Test slug generation removes special characters."""
        assert generate_slug("Data & Analytics") == "data-analytics"
        assert (
            generate_slug("Machine Learning (Advanced)") == "machine-learning-advanced"
        )
        assert generate_slug("C++ Programming") == "c-programming"


class TestAddCourse:
    """Test add_course function."""

    @pytest.fixture
    def sample_university(self, app, db):
        """Create a sample university for testing."""
        with app.app_context():
            university = University(name="Test University", slug="test-university")
            db.session.add(university)
            db.session.commit()
            # Return the ID, not the object, to avoid detached instance issues
            return university.id

    def test_add_course_success(self, app, db, sample_university):
        """Test adding a course successfully."""
        with app.app_context():
            course = add_course(
                name="Introduction to Statistics",
                semester="2023_SoSe",
                university_id=sample_university,
            )

            assert course is not None
            assert course.id is not None
            assert course.name == "Introduction to Statistics"
            assert course.semester == "2023_SoSe"
            assert course.university_id == sample_university
            assert course.slug == "introduction-to-statistics"

    def test_add_course_with_custom_slug(self, app, db, sample_university):
        """Test adding a course with custom slug."""
        with app.app_context():
            course = add_course(
                name="Introduction to Statistics",
                semester="2023_SoSe",
                university_id=sample_university,
                slug="intro-stats",
            )

            assert course.slug == "intro-stats"

    def test_add_course_strips_whitespace(self, app, db, sample_university):
        """Test that whitespace is stripped from fields."""
        with app.app_context():
            course = add_course(
                name="  Introduction to Statistics  ",
                semester=" 2023_SoSe ",
                university_id=sample_university,
            )

            assert course.name == "Introduction to Statistics"
            assert course.semester == "2023_SoSe"

    def test_add_course_empty_name(self, app, db, sample_university):
        """Test that empty name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Course name cannot be empty"):
                add_course(
                    name="",
                    semester="2023_SoSe",
                    university_id=sample_university,
                )

    def test_add_course_invalid_semester(self, app, db, sample_university):
        """Test that invalid semester format raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid semester format"):
                add_course(
                    name="Introduction to Statistics",
                    semester="2023",
                    university_id=sample_university,
                )

    def test_add_course_invalid_university(self, app, db):
        """Test that non-existent university raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="University with ID 999 not found"):
                add_course(
                    name="Introduction to Statistics",
                    semester="2023_SoSe",
                    university_id=999,
                )

    def test_add_course_duplicate_slug_same_semester(self, app, db, sample_university):
        """Test that duplicate slug in same semester raises IntegrityError."""
        with app.app_context():
            # Add first course
            add_course(
                name="Introduction to Statistics",
                semester="2023_SoSe",
                university_id=sample_university,
            )

            # Try to add course with same slug in same semester
            from sqlalchemy.exc import IntegrityError

            with pytest.raises(IntegrityError):
                add_course(
                    name="Introduction to Statistics",
                    semester="2023_SoSe",
                    university_id=sample_university,
                )

    def test_add_course_same_slug_different_semester(self, app, db, sample_university):
        """Test that same slug is allowed in different semesters."""
        with app.app_context():
            # Add first course in summer semester
            course1 = add_course(
                name="Introduction to Statistics",
                semester="2023_SoSe",
                university_id=sample_university,
            )

            # Add same course in winter semester
            course2 = add_course(
                name="Introduction to Statistics",
                semester="2023_WiSe",
                university_id=sample_university,
            )

            assert course1 is not None
            assert course2 is not None
            assert course1.slug == course2.slug
            assert course1.semester != course2.semester


class TestListCourses:
    """Test list_courses function."""

    @pytest.fixture
    def sample_courses(self, app, db):
        """Create sample courses for testing."""
        with app.app_context():
            # Create universities
            uni1 = University(name="University A", slug="university-a")
            uni2 = University(name="University B", slug="university-b")
            db.session.add_all([uni1, uni2])
            db.session.commit()

            # Store IDs before creating courses
            uni1_id = uni1.id
            uni2_id = uni2.id

            # Create courses
            add_course("Statistics I", "2023_SoSe", uni1_id)
            add_course("Statistics II", "2023_WiSe", uni1_id)
            add_course("Data Science", "2023_SoSe", uni2_id)

            return {"uni1": uni1_id, "uni2": uni2_id}

    def test_list_all_courses(self, app, db, sample_courses):
        """Test listing all courses."""
        with app.app_context():
            courses = list_courses()
            assert len(courses) == 3

    def test_list_courses_filter_by_university(self, app, db, sample_courses):
        """Test filtering courses by university."""
        with app.app_context():
            uni1_courses = list_courses(university_id=sample_courses["uni1"])
            assert len(uni1_courses) == 2

            uni2_courses = list_courses(university_id=sample_courses["uni2"])
            assert len(uni2_courses) == 1

    def test_list_courses_filter_by_semester(self, app, db, sample_courses):
        """Test filtering courses by semester."""
        with app.app_context():
            summer_courses = list_courses(semester="2023_SoSe")
            assert len(summer_courses) == 2

            winter_courses = list_courses(semester="2023_WiSe")
            assert len(winter_courses) == 1

    def test_list_courses_filter_both(self, app, db, sample_courses):
        """Test filtering courses by both university and semester."""
        with app.app_context():
            courses = list_courses(
                university_id=sample_courses["uni1"], semester="2023_SoSe"
            )
            assert len(courses) == 1
            assert courses[0].name == "Statistics I"


class TestGetCourse:
    """Test get_course function."""

    @pytest.fixture
    def sample_course(self, app, db):
        """Create a sample course for testing."""
        with app.app_context():
            university = University(name="Test University", slug="test-university")
            db.session.add(university)
            db.session.commit()

            course = add_course(
                name="Introduction to Statistics",
                semester="2023_SoSe",
                university_id=university.id,
            )
            return course.id

    def test_get_course_success(self, app, db, sample_course):
        """Test getting a course by ID."""
        with app.app_context():
            course = get_course(sample_course)
            assert course is not None
            assert course.id == sample_course
            assert course.name == "Introduction to Statistics"

    def test_get_course_not_found(self, app, db):
        """Test getting a non-existent course."""
        with app.app_context():
            course = get_course(999)
            assert course is None


class TestUpdateCourse:
    """Test update_course function."""

    @pytest.fixture
    def sample_course(self, app, db):
        """Create a sample course for testing."""
        with app.app_context():
            university = University(name="Test University", slug="test-university")
            db.session.add(university)
            db.session.commit()

            course = add_course(
                name="Introduction to Statistics",
                semester="2023_SoSe",
                university_id=university.id,
            )
            return course.id

    def test_update_course_name(self, app, db, sample_course):
        """Test updating course name."""
        with app.app_context():
            updated = update_course(sample_course, name="Advanced Statistics")
            assert updated is not None
            assert updated.name == "Advanced Statistics"
            assert updated.slug == "advanced-statistics"  # Slug should be regenerated

    def test_update_course_semester(self, app, db, sample_course):
        """Test updating course semester."""
        with app.app_context():
            updated = update_course(sample_course, semester="2024_WiSe")
            assert updated is not None
            assert updated.semester == "2024_WiSe"

    def test_update_course_slug(self, app, db, sample_course):
        """Test updating course slug."""
        with app.app_context():
            updated = update_course(sample_course, slug="intro-stats")
            assert updated is not None
            assert updated.slug == "intro-stats"

    def test_update_course_name_with_custom_slug(self, app, db, sample_course):
        """Test updating course name with custom slug."""
        with app.app_context():
            updated = update_course(
                sample_course, name="Advanced Statistics", slug="adv-stats"
            )
            assert updated is not None
            assert updated.name == "Advanced Statistics"
            assert updated.slug == "adv-stats"  # Custom slug should be used

    def test_update_course_invalid_semester(self, app, db, sample_course):
        """Test updating with invalid semester format."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid semester format"):
                update_course(sample_course, semester="2024")

    def test_update_course_not_found(self, app, db):
        """Test updating non-existent course."""
        with app.app_context():
            with pytest.raises(ValueError, match="Course with ID 999 not found"):
                update_course(999, name="New Name")


class TestDeleteCourse:
    """Test delete_course function."""

    @pytest.fixture
    def sample_course(self, app, db):
        """Create a sample course for testing."""
        with app.app_context():
            university = University(name="Test University", slug="test-university")
            db.session.add(university)
            db.session.commit()

            course = add_course(
                name="Introduction to Statistics",
                semester="2023_SoSe",
                university_id=university.id,
            )
            return course.id

    def test_delete_course_success(self, app, db, sample_course):
        """Test deleting a course."""
        with app.app_context():
            result = delete_course(sample_course)
            assert result is True

            # Verify course is deleted
            course = get_course(sample_course)
            assert course is None

    def test_delete_course_not_found(self, app, db):
        """Test deleting non-existent course."""
        with app.app_context():
            with pytest.raises(ValueError, match="Course with ID 999 not found"):
                delete_course(999)
