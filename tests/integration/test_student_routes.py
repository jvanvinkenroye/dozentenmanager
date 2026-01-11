"""
Integration tests for student routes.

This module tests the Flask web interface for student management.
"""

import pytest

from app.services.student_service import StudentService


@pytest.fixture
def service():
    """Return a StudentService instance."""
    return StudentService()


class TestStudentIndexRoute:
    """Test student list route."""

    def test_index_empty(self, app, client, service):
        """Test listing students when none exist."""
        with app.app_context():
            response = client.get("/students/")
            assert response.status_code == 200
            # Just check page loads correctly
            assert b"Studierende" in response.data

    def test_index_with_students(self, app, client, service):
        """Test listing students with data."""
        with app.app_context():
            service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )
            service.add_student(
                first_name="Anna",
                last_name="Schmidt",
                student_id="87654321",
                email="anna@example.com",
                program="Mathematik",
            )

            response = client.get("/students/")
            assert response.status_code == 200
            assert b"Mustermann" in response.data
            assert b"Schmidt" in response.data
            # Check both students appear in listing
            assert response.status_code == 200

    def test_index_with_search(self, app, client, service):
        """Test searching students."""
        with app.app_context():
            service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )
            service.add_student(
                first_name="Anna",
                last_name="Schmidt",
                student_id="87654321",
                email="anna@example.com",
                program="Mathematik",
            )

            # Search by name
            response = client.get("/students/?search=Mustermann")
            assert response.status_code == 200
            assert b"Mustermann" in response.data
            assert b"Schmidt" not in response.data

    def test_index_search_by_email(self, app, client, service):
        """Test searching students by email."""
        with app.app_context():
            service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )
            service.add_student(
                first_name="Anna",
                last_name="Schmidt",
                student_id="87654321",
                email="anna@example.com",
                program="Mathematik",
            )

            response = client.get("/students/?search=anna@")
            assert response.status_code == 200
            assert b"Schmidt" in response.data
            assert b"Mustermann" not in response.data

    def test_index_search_by_student_id(self, app, client, service):
        """Test searching students by student ID."""
        with app.app_context():
            service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )
            service.add_student(
                first_name="Anna",
                last_name="Schmidt",
                student_id="87654321",
                email="anna@example.com",
                program="Mathematik",
            )

            response = client.get("/students/?search=87654321")
            assert response.status_code == 200
            assert b"Schmidt" in response.data
            assert b"Mustermann" not in response.data


class TestStudentShowRoute:
    """Test student detail route."""

    def test_show_existing_student(self, app, client, service):
        """Test showing details of existing student."""
        with app.app_context():
            student = service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )

            response = client.get(f"/students/{student.id}")
            assert response.status_code == 200
            assert b"Mustermann" in response.data
            assert b"12345678" in response.data
            assert b"max@example.com" in response.data

    def test_show_nonexistent_student(self, app, client, service):
        """Test showing details of non-existent student."""
        with app.app_context():
            response = client.get("/students/999")
            assert response.status_code == 302  # Redirect
            assert b"/students/" in response.data  # Redirects to list


class TestStudentNewRoute:
    """Test student creation route."""

    def test_new_get(self, app, client, service):
        """Test GET request to new student form."""
        with app.app_context():
            response = client.get("/students/new")
            assert response.status_code == 200
            assert b"Studierende" in response.data
            assert b"Vorname" in response.data or b"vorname" in response.data

    def test_new_post_success(self, app, client, service):
        """Test POST request to create new student."""
        with app.app_context():
            response = client.post(
                "/students/new",
                data={
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "student_id": "12345678",
                    "email": "max@example.com",
                    "program": "Informatik",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302  # Redirect to detail page

            # Verify student was created
            from app import db
            from app.models.student import Student

            student = db.session.query(Student).filter_by(student_id="12345678").first()
            assert student is not None
            assert student.first_name == "Max"
            assert student.last_name == "Mustermann"
            assert student.email == "max@example.com"

            # Verify redirects to detail page
            assert f"/students/{student.id}".encode() in response.data

    def test_new_post_empty_first_name(self, app, client, service):
        """Test POST request with empty first name."""
        with app.app_context():
            response = client.post(
                "/students/new",
                data={
                    "first_name": "",
                    "last_name": "Mustermann",
                    "student_id": "12345678",
                    "email": "max@example.com",
                    "program": "Informatik",
                },
            )

            assert response.status_code == 200  # Stays on form
            # Form validation should catch this

    def test_new_post_invalid_email(self, app, client, service):
        """Test POST request with invalid email."""
        with app.app_context():
            response = client.post(
                "/students/new",
                data={
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "student_id": "12345678",
                    "email": "not-an-email",
                    "program": "Informatik",
                },
            )

            assert response.status_code == 200
            # Should show validation error

    def test_new_post_duplicate_student_id(self, app, client, service):
        """Test POST request with duplicate student ID."""
        with app.app_context():
            service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )

            response = client.post(
                "/students/new",
                data={
                    "first_name": "Anna",
                    "last_name": "Schmidt",
                    "student_id": "12345678",  # Duplicate
                    "email": "anna@example.com",
                    "program": "Mathematik",
                },
            )

            assert response.status_code == 200
            assert (
                b"already exists" in response.data
                or b"existiert bereits" in response.data
            )

    def test_new_post_duplicate_email(self, app, client, service):
        """Test POST request with duplicate email."""
        with app.app_context():
            service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )

            response = client.post(
                "/students/new",
                data={
                    "first_name": "Anna",
                    "last_name": "Schmidt",
                    "student_id": "87654321",
                    "email": "max@example.com",  # Duplicate
                    "program": "Mathematik",
                },
            )

            assert response.status_code == 200
            assert (
                b"already exists" in response.data
                or b"existiert bereits" in response.data
            )


class TestStudentEditRoute:
    """Test student edit route."""

    def test_edit_get(self, app, client, service):
        """Test GET request to edit student form."""
        with app.app_context():
            student = service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )

            response = client.get(f"/students/{student.id}/edit")
            assert response.status_code == 200
            assert b"bearbeiten" in response.data
            assert b"Mustermann" in response.data

    def test_edit_get_nonexistent(self, app, client, service):
        """Test GET request to edit non-existent student."""
        with app.app_context():
            response = client.get("/students/999/edit")
            assert response.status_code == 302  # Redirect

    def test_edit_post_success(self, app, client, service):
        """Test POST request to update student."""
        with app.app_context():
            student = service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )

            response = client.post(
                f"/students/{student.id}/edit",
                data={
                    "first_name": "Maximilian",
                    "last_name": "Mustermann",
                    "student_id": "12345678",
                    "email": "maximilian@example.com",
                    "program": "Computer Science",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302  # Redirect to detail page
            assert f"/students/{student.id}".encode() in response.data

            # Verify update
            from app import db
            from app.models.student import Student

            updated = db.session.query(Student).filter_by(id=student.id).first()
            assert updated.first_name == "Maximilian"
            assert updated.email == "maximilian@example.com"
            assert updated.program == "Computer Science"

    def test_edit_post_empty_name(self, app, client, service):
        """Test POST request with empty name."""
        with app.app_context():
            student = service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )

            response = client.post(
                f"/students/{student.id}/edit",
                data={
                    "first_name": "",
                    "last_name": "Mustermann",
                    "student_id": "12345678",
                    "email": "max@example.com",
                    "program": "Informatik",
                },
            )

            assert response.status_code == 200
            # Should show validation error

    def test_edit_post_invalid_email(self, app, client, service):
        """Test POST request with invalid email."""
        with app.app_context():
            student = service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )

            response = client.post(
                f"/students/{student.id}/edit",
                data={
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "student_id": "12345678",
                    "email": "invalid-email",
                    "program": "Informatik",
                },
            )

            assert response.status_code == 200
            # Should show validation error


class TestStudentDeleteRoute:
    """Test student delete route."""

    def test_delete_get(self, app, client, service):
        """Test GET request to delete confirmation page."""
        with app.app_context():
            student = service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )

            response = client.get(f"/students/{student.id}/delete")
            assert response.status_code == 200
            assert b"schen" in response.data  # "löschen" with encoding
            assert b"Mustermann" in response.data

    def test_delete_get_nonexistent(self, app, client, service):
        """Test GET request to delete non-existent student."""
        with app.app_context():
            response = client.get("/students/999/delete")
            assert response.status_code == 302

    def test_delete_post_success(self, app, client, service):
        """Test POST request to delete student."""
        with app.app_context():
            student = service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Informatik",
            )
            student_id = student.id

            response = client.post(
                f"/students/{student_id}/delete", follow_redirects=False
            )

            assert response.status_code == 302
            assert b"/students/" in response.data

            # Verify deletion
            from app import db
            from app.models.student import Student

            deleted = db.session.query(Student).filter_by(id=student_id).first()
            assert deleted is None

    def test_delete_post_nonexistent(self, app, client, service):
        """Test POST request to delete non-existent student."""
        with app.app_context():
            response = client.post("/students/999/delete", follow_redirects=False)
            assert response.status_code == 302
