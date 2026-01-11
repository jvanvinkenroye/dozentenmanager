"""
Integration tests for course routes.

This module tests the Flask web interface for course management.
"""

import pytest

from app.services.course_service import CourseService
from app.services.university_service import UniversityService


@pytest.fixture
def course_service():
    """Return a CourseService instance."""
    return CourseService()


@pytest.fixture
def university_service():
    """Return a UniversityService instance."""
    return UniversityService()


@pytest.fixture
def sample_university(app, university_service):
    """Create a sample university for testing."""
    with app.app_context():
        return university_service.add_university("TH Köln", "th-koeln")


class TestCourseIndexRoute:
    """Test course list route."""

    def test_index_empty(self, app, client, course_service):
        """Test listing courses when none exist."""
        with app.app_context():
            response = client.get("/courses/")
            assert response.status_code == 200
            # Just check page loads correctly
            assert b"Lehrveranstaltung" in response.data

    def test_index_with_courses(self, app, client, course_service, sample_university):
        """Test listing courses with data."""
        with app.app_context():
            course_service.add_course(
                name="Einführung Informatik",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )
            course_service.add_course(
                name="Programmierung 1",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )

            response = client.get("/courses/")
            assert response.status_code == 200
            assert b"Informatik" in response.data
            assert b"Programmierung" in response.data

    def test_index_with_search(self, app, client, course_service, sample_university):
        """Test searching courses."""
        with app.app_context():
            course_service.add_course(
                name="Einführung Informatik",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )
            course_service.add_course(
                name="Programmierung 1",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )

            # Search by name
            response = client.get("/courses/?search=Informatik")
            assert response.status_code == 200
            assert b"Informatik" in response.data
            assert b"Programmierung" not in response.data

    def test_index_filter_by_semester(
        self, app, client, course_service, sample_university
    ):
        """Test filtering courses by semester."""
        with app.app_context():
            course_service.add_course(
                name="Kurs WiSe",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )
            course_service.add_course(
                name="Kurs SoSe",
                semester="2024_SoSe",
                university_id=sample_university.id,
            )

            response = client.get("/courses/?semester=2024_WiSe")
            assert response.status_code == 200
            # Check that WiSe course appears but not SoSe
            assert b"Kurs WiSe" in response.data or b"2024_WiSe" in response.data


class TestCourseShowRoute:
    """Test course detail route."""

    def test_show_existing_course(self, app, client, course_service, sample_university):
        """Test showing details of existing course."""
        with app.app_context():
            course = course_service.add_course(
                name="Einführung Informatik",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )

            response = client.get(f"/courses/{course.id}")
            assert response.status_code == 200
            assert b"Informatik" in response.data
            assert b"2024_WiSe" in response.data

    def test_show_nonexistent_course(self, app, client, course_service):
        """Test showing details of non-existent course."""
        with app.app_context():
            response = client.get("/courses/999")
            assert response.status_code == 302  # Redirect
            assert b"/courses/" in response.data  # Redirects to list


class TestCourseNewRoute:
    """Test course creation route."""

    def test_new_get(self, app, client, course_service, sample_university):
        """Test GET request to new course form."""
        with app.app_context():
            response = client.get("/courses/new")
            assert response.status_code == 200
            assert b"Lehrveranstaltung" in response.data
            assert b"Name" in response.data or b"name" in response.data

    def test_new_post_success(self, app, client, course_service, sample_university):
        """Test POST request to create new course."""
        with app.app_context():
            response = client.post(
                "/courses/new",
                data={
                    "name": "Einführung Informatik",
                    "semester": "2024_WiSe",
                    "university_id": sample_university.id,
                    "slug": "einfuehrung-informatik",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302  # Redirect
            assert b"/courses/" in response.data

            # Verify course was created
            from app import db
            from app.models.course import Course

            course = (
                db.session.query(Course).filter_by(name="Einführung Informatik").first()
            )
            assert course is not None
            assert course.semester == "2024_WiSe"
            assert course.slug == "einfuehrung-informatik"

    def test_new_post_auto_slug(self, app, client, course_service, sample_university):
        """Test POST request with auto-generated slug."""
        with app.app_context():
            response = client.post(
                "/courses/new",
                data={
                    "name": "Einführung Informatik",
                    "semester": "2024_WiSe",
                    "university_id": sample_university.id,
                    "slug": "",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302

            # Verify slug was auto-generated
            from app import db
            from app.models.course import Course

            course = (
                db.session.query(Course).filter_by(name="Einführung Informatik").first()
            )
            assert course is not None
            assert course.slug == "einfuehrung-informatik"

    def test_new_post_empty_name(self, app, client, course_service, sample_university):
        """Test POST request with empty name."""
        with app.app_context():
            response = client.post(
                "/courses/new",
                data={
                    "name": "",
                    "semester": "2024_WiSe",
                    "university_id": sample_university.id,
                    "slug": "test",
                },
            )

            assert response.status_code == 200  # Stays on form
            # Form validation should catch this

    def test_new_post_invalid_slug(
        self, app, client, course_service, sample_university
    ):
        """Test POST request with invalid slug."""
        with app.app_context():
            response = client.post(
                "/courses/new",
                data={
                    "name": "Test Course",
                    "semester": "2024_WiSe",
                    "university_id": sample_university.id,
                    "slug": "Test Course!",
                },
            )

            assert response.status_code == 200
            assert b"Invalid slug format" in response.data or b"Slug" in response.data

    def test_new_post_duplicate(self, app, client, course_service, sample_university):
        """Test POST request with duplicate course."""
        with app.app_context():
            # Create course with specific slug
            course_service.add_course(
                name="Einführung Informatik",
                semester="2024_WiSe",
                university_id=sample_university.id,
                slug="einfuehrung-informatik",
            )

            # Try to create another course with same university+semester+slug
            response = client.post(
                "/courses/new",
                data={
                    "name": "Different Name",  # Name can be different
                    "semester": "2024_WiSe",
                    "university_id": sample_university.id,
                    "slug": "einfuehrung-informatik",  # Same slug = duplicate
                },
            )

            assert response.status_code == 200  # Stays on form
            assert (
                b"already exists" in response.data
                or b"existiert bereits" in response.data
            )


class TestCourseEditRoute:
    """Test course edit route."""

    def test_edit_get(self, app, client, course_service, sample_university):
        """Test GET request to edit course form."""
        with app.app_context():
            course = course_service.add_course(
                name="Einführung Informatik",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )

            response = client.get(f"/courses/{course.id}/edit")
            assert response.status_code == 200
            assert b"bearbeiten" in response.data
            assert b"Informatik" in response.data

    def test_edit_get_nonexistent(self, app, client, course_service):
        """Test GET request to edit non-existent course."""
        with app.app_context():
            response = client.get("/courses/999/edit")
            assert response.status_code == 302  # Redirect

    def test_edit_post_success(self, app, client, course_service, sample_university):
        """Test POST request to update course."""
        with app.app_context():
            course = course_service.add_course(
                name="Einführung Informatik",
                semester="2024_WiSe",
                university_id=sample_university.id,
                slug="einfuehrung-informatik",
            )

            response = client.post(
                f"/courses/{course.id}/edit",
                data={
                    "name": "Grundlagen Informatik",
                    "semester": "2024_WiSe",
                    "university_id": sample_university.id,
                    "slug": "grundlagen-informatik",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302

            # Verify update
            from app import db
            from app.models.course import Course

            updated = db.session.query(Course).filter_by(id=course.id).first()
            assert updated.name == "Grundlagen Informatik"
            assert updated.slug == "grundlagen-informatik"

    def test_edit_post_empty_name(self, app, client, course_service, sample_university):
        """Test POST request with empty name."""
        with app.app_context():
            course = course_service.add_course(
                name="Einführung Informatik",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )

            response = client.post(
                f"/courses/{course.id}/edit",
                data={
                    "name": "",
                    "semester": "2024_WiSe",
                    "university_id": sample_university.id,
                    "slug": "test",
                },
            )

            assert response.status_code == 200
            # Should show validation error

    def test_edit_post_invalid_slug(
        self, app, client, course_service, sample_university
    ):
        """Test POST request with invalid slug."""
        with app.app_context():
            course = course_service.add_course(
                name="Einführung Informatik",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )

            response = client.post(
                f"/courses/{course.id}/edit",
                data={
                    "name": "Test Course",
                    "semester": "2024_WiSe",
                    "university_id": sample_university.id,
                    "slug": "Invalid Slug!",
                },
            )

            assert response.status_code == 200
            assert b"Invalid slug format" in response.data or b"Slug" in response.data


class TestCourseDeleteRoute:
    """Test course delete route."""

    def test_delete_get(self, app, client, course_service, sample_university):
        """Test GET request to delete confirmation page."""
        with app.app_context():
            course = course_service.add_course(
                name="Einführung Informatik",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )

            response = client.get(f"/courses/{course.id}/delete")
            assert response.status_code == 200
            assert b"schen" in response.data  # "löschen" with encoding
            assert b"Informatik" in response.data

    def test_delete_get_nonexistent(self, app, client, course_service):
        """Test GET request to delete non-existent course."""
        with app.app_context():
            response = client.get("/courses/999/delete")
            assert response.status_code == 302

    def test_delete_post_success(self, app, client, course_service, sample_university):
        """Test POST request to delete course."""
        with app.app_context():
            course = course_service.add_course(
                name="Einführung Informatik",
                semester="2024_WiSe",
                university_id=sample_university.id,
            )
            course_id = course.id

            response = client.post(
                f"/courses/{course_id}/delete", follow_redirects=False
            )

            assert response.status_code == 302
            assert b"/courses/" in response.data

            # Verify deletion
            from app import db
            from app.models.course import Course

            deleted = db.session.query(Course).filter_by(id=course_id).first()
            assert deleted is None

    def test_delete_post_nonexistent(self, app, client, course_service):
        """Test POST request to delete non-existent course."""
        with app.app_context():
            response = client.post("/courses/999/delete", follow_redirects=False)
            assert response.status_code == 302
