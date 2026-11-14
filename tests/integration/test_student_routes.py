"""
Integration tests for student routes.

This module tests the Flask web interface for student management.
"""

import io
import re

import pytest

from app.services.student_service import StudentService


@pytest.fixture
def service():
    """Return a StudentService instance."""
    return StudentService()


class TestStudentIndexRoute:
    """Test student list route."""

    def test_index_empty(self, app, auth_client, service):
        """Test listing students when none exist."""
        response = auth_client.get("/students/")
        assert response.status_code == 200
        # Just check page loads correctly
        assert b"Studierende" in response.data

    def test_index_with_students(self, app, auth_client, service):
        """Test listing students with data."""
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

        response = auth_client.get("/students/")
        assert response.status_code == 200
        assert b"Mustermann" in response.data
        assert b"Schmidt" in response.data
        # Check both students appear in listing
        assert response.status_code == 200

    def test_index_with_search(self, app, auth_client, service):
        """Test searching students."""
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
        response = auth_client.get("/students/?search=Mustermann")
        assert response.status_code == 200
        assert b"Mustermann" in response.data
        assert b"Schmidt" not in response.data

    def test_index_search_by_email(self, app, auth_client, service):
        """Test searching students by email."""
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

        response = auth_client.get("/students/?search=anna@")
        assert response.status_code == 200
        assert b"Schmidt" in response.data
        assert b"Mustermann" not in response.data

    def test_index_search_by_student_id(self, app, auth_client, service):
        """Test searching students by student ID."""
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

        response = auth_client.get("/students/?search=87654321")
        assert response.status_code == 200
        assert b"Schmidt" in response.data
        assert b"Mustermann" not in response.data


class TestStudentShowRoute:
    """Test student detail route."""

    def test_show_existing_student(self, app, auth_client, service):
        """Test showing details of existing student."""
        student = service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )

        response = auth_client.get(f"/students/{student.id}")
        assert response.status_code == 200
        assert b"Mustermann" in response.data
        assert b"12345678" in response.data
        assert b"max@example.com" in response.data

    def test_show_nonexistent_student(self, app, auth_client, service):
        """Test showing details of non-existent student."""
        response = auth_client.get("/students/999")
        assert response.status_code == 302  # Redirect
        assert b"/students/" in response.data  # Redirects to list


class TestStudentNewRoute:
    """Test student creation route."""

    def test_new_get(self, app, auth_client, service):
        """Test GET request to new student form."""
        response = auth_client.get("/students/new")
        assert response.status_code == 200
        assert b"Studierende" in response.data
        assert b"Vorname" in response.data or b"vorname" in response.data

    def test_new_post_success(self, app, auth_client, service):
        """Test POST request to create new student."""
        response = auth_client.post(
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

    def test_new_post_empty_first_name(self, app, auth_client, service):
        """Test POST request with empty first name."""
        response = auth_client.post(
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

    def test_new_post_invalid_email(self, app, auth_client, service):
        """Test POST request with invalid email."""
        response = auth_client.post(
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

    def test_new_post_duplicate_student_id(self, app, auth_client, service):
        """Test POST request with duplicate student ID."""
        service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )

        response = auth_client.post(
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
            b"already exists" in response.data or b"existiert bereits" in response.data
        )

    def test_new_post_duplicate_email(self, app, auth_client, service):
        """Test POST request with duplicate email."""
        service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )

        response = auth_client.post(
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
            b"already exists" in response.data or b"existiert bereits" in response.data
        )


class TestStudentEditRoute:
    """Test student edit route."""

    def test_edit_get(self, app, auth_client, service):
        """Test GET request to edit student form."""
        student = service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )

        response = auth_client.get(f"/students/{student.id}/edit")
        assert response.status_code == 200
        assert b"bearbeiten" in response.data
        assert b"Mustermann" in response.data

    def test_edit_get_nonexistent(self, app, auth_client, service):
        """Test GET request to edit non-existent student."""
        response = auth_client.get("/students/999/edit")
        assert response.status_code == 302  # Redirect

    def test_edit_post_success(self, app, auth_client, service):
        """Test POST request to update student."""
        student = service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )

        response = auth_client.post(
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

    def test_edit_post_empty_name(self, app, auth_client, service):
        """Test POST request with empty name."""
        student = service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )

        response = auth_client.post(
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

    def test_edit_post_invalid_email(self, app, auth_client, service):
        """Test POST request with invalid email."""
        student = service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )

        response = auth_client.post(
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

    def test_delete_get(self, app, auth_client, service):
        """Test GET request to delete confirmation page."""
        student = service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )

        response = auth_client.get(f"/students/{student.id}/delete")
        assert response.status_code == 200
        assert b"schen" in response.data  # "löschen" with encoding
        assert b"Mustermann" in response.data

    def test_delete_get_nonexistent(self, app, auth_client, service):
        """Test GET request to delete non-existent student."""
        response = auth_client.get("/students/999/delete")
        assert response.status_code == 302

    def test_delete_post_success(self, app, auth_client, service):
        """Test POST request to delete student."""
        student = service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )
        student_id = student.id

        response = auth_client.post(
            f"/students/{student_id}/delete", follow_redirects=False
        )

        assert response.status_code == 302
        assert b"/students/" in response.data

        # Verify deletion
        from app import db
        from app.models.student import Student

        deleted = db.session.query(Student).filter_by(id=student_id).first()
        assert deleted is not None
        assert deleted.deleted_at is not None

    def test_delete_post_nonexistent(self, app, auth_client, service):
        """Test POST request to delete non-existent student."""
        response = auth_client.post("/students/999/delete", follow_redirects=False)
        assert response.status_code == 302


class TestStudentExportRoute:
    """Test student CSV export route."""

    def _add_students(self, service):
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

    def test_export_all_students(self, app, auth_client, service):
        """Export returns a CSV attachment containing all students."""
        self._add_students(service)

        response = auth_client.get("/students/export")
        assert response.status_code == 200
        assert response.mimetype == "text/csv"
        assert "attachment" in response.headers["Content-Disposition"]

        body = response.data.decode("utf-8")
        assert "first_name,last_name,student_id,email,program" in body
        assert "Max,Mustermann,12345678,max@example.com,Informatik" in body
        assert "Anna,Schmidt,87654321,anna@example.com,Mathematik" in body

    def test_export_with_search_filter(self, app, auth_client, service):
        """Search filter limits the exported rows."""
        self._add_students(service)

        response = auth_client.get("/students/export?search=Mustermann")
        body = response.data.decode("utf-8")
        assert "Mustermann" in body
        assert "Schmidt" not in body

    def test_export_with_program_filter(self, app, auth_client, service):
        """Program filter limits the exported rows."""
        self._add_students(service)

        response = auth_client.get("/students/export?program=Mathematik")
        body = response.data.decode("utf-8")
        assert "Schmidt" in body
        assert "Mustermann" not in body

    def test_export_requires_login(self, app, client):
        """Anonymous users are redirected to login."""
        response = client.get("/students/export")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]


VALID_IMPORT_CSV = (
    "first_name,last_name,student_id,email,program\n"
    "Max,Mustermann,12345678,max@example.com,Informatik\n"
    "Anna,Schmidt,87654321,anna@example.com,Mathematik\n"
)


class TestStudentImportRoute:
    """Test the two-step student import flow (upload, then mapping)."""

    def _upload(self, auth_client, csv_text, on_duplicate="skip"):
        """Step 1: upload the file and return the rendered mapping page."""
        return auth_client.post(
            "/students/import",
            data={
                "file": (io.BytesIO(csv_text.encode("utf-8")), "students.csv"),
                "file_format": "csv",
                "on_duplicate": on_duplicate,
            },
            content_type="multipart/form-data",
        )

    def _extract_token(self, page):
        """Read the mapping token out of the rendered mapping form."""
        match = re.search(r'name="mapping_token" value="([0-9a-f]+)"', page)
        assert match, "mapping form with token expected in response"
        return match.group(1)

    def _submit_mapping(self, auth_client, token, on_duplicate="skip"):
        """Step 2: confirm the identity column mapping."""
        return auth_client.post(
            "/students/import",
            data={
                "mapping_token": token,
                "file_format": "csv",
                "file_extension": "csv",
                "on_duplicate": on_duplicate,
                "map_first_name": "first_name",
                "map_last_name": "last_name",
                "map_student_id": "student_id",
                "map_email": "email",
                "map_program": "program",
            },
        )

    def test_import_form_get(self, app, auth_client):
        """The import form renders."""
        response = auth_client.get("/students/import")
        assert response.status_code == 200

    def test_import_full_flow_creates_students(self, app, auth_client, service):
        """Uploading a valid CSV and confirming the mapping creates students."""
        upload = self._upload(auth_client, VALID_IMPORT_CSV)
        assert upload.status_code == 200
        token = self._extract_token(upload.data.decode("utf-8"))

        result = self._submit_mapping(auth_client, token)
        page = result.data.decode("utf-8")
        assert "Import abgeschlossen" in page
        assert "Neu: 2" in page
        assert "Fehler: 0" in page

        students = service.list_students()
        assert {s.student_id for s in students} == {"12345678", "87654321"}

    def test_import_duplicate_skip(self, app, auth_client, service):
        """Existing students are skipped with on_duplicate=skip."""
        service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )
        upload = self._upload(auth_client, VALID_IMPORT_CSV)
        token = self._extract_token(upload.data.decode("utf-8"))

        result = self._submit_mapping(auth_client, token)
        page = result.data.decode("utf-8")
        assert "Neu: 1" in page
        assert "Übersprungen: 1" in page

    def test_import_duplicate_update(self, app, auth_client, service):
        """Existing students are updated with on_duplicate=update."""
        service.add_student(
            first_name="Old",
            last_name="Name",
            student_id="12345678",
            email="max@example.com",
            program="Alt",
        )
        upload = self._upload(auth_client, VALID_IMPORT_CSV, on_duplicate="update")
        token = self._extract_token(upload.data.decode("utf-8"))

        result = self._submit_mapping(auth_client, token, on_duplicate="update")
        page = result.data.decode("utf-8")
        assert "Aktualisiert: 1" in page
        assert "Neu: 1" in page

        updated = next(s for s in service.list_students() if s.student_id == "12345678")
        assert updated.first_name == "Max"
        assert updated.program == "Informatik"

    def test_import_invalid_email_reports_error(self, app, auth_client, service):
        """Rows with invalid emails are reported as errors."""
        csv_text = (
            "first_name,last_name,student_id,email,program\n"
            "Max,Mustermann,12345678,not-an-email,Informatik\n"
        )
        upload = self._upload(auth_client, csv_text)
        token = self._extract_token(upload.data.decode("utf-8"))

        result = self._submit_mapping(auth_client, token)
        page = result.data.decode("utf-8")
        assert "Fehler: 1" in page
        assert "ungültige E-Mail" in page
        assert service.list_students() == []

    def test_import_duplicate_within_file(self, app, auth_client, service):
        """Duplicate rows within the same file are counted as errors."""
        csv_text = (
            "first_name,last_name,student_id,email,program\n"
            "Max,Mustermann,12345678,max@example.com,Informatik\n"
            "Max,Mustermann,12345678,max2@example.com,Informatik\n"
        )
        upload = self._upload(auth_client, csv_text)
        token = self._extract_token(upload.data.decode("utf-8"))

        result = self._submit_mapping(auth_client, token)
        page = result.data.decode("utf-8")
        assert "Neu: 1" in page
        assert "Duplikat innerhalb der Datei" in page

    def test_import_rejects_wrong_extension(self, app, auth_client):
        """Files with disallowed extensions are rejected by the form."""
        response = auth_client.post(
            "/students/import",
            data={
                "file": (io.BytesIO(b"some text"), "students.txt"),
                "file_format": "",
                "on_duplicate": "skip",
            },
            content_type="multipart/form-data",
        )
        assert "Nur CSV, XLSX oder XLS" in response.data.decode("utf-8")

    def test_import_unknown_token_redirects(self, app, auth_client):
        """A stale mapping token redirects back to the upload form."""
        response = self._submit_mapping(auth_client, "0" * 32)
        assert response.status_code == 302
