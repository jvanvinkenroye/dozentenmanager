"""
Integration tests for document routes.

This module tests the document management web routes including
document upload, listing, and deletion functionality.
"""

import io
import pytest
from flask import url_for

from app import create_app, db
from app.models import Course, Document, Enrollment, Student, Submission, University


@pytest.fixture
def app():
    """Create and configure test application."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_data(app):
    """Create sample data for testing."""
    with app.app_context():
        # Create university
        university = University(name="Test University", slug="test-uni")
        db.session.add(university)
        db.session.flush()

        # Create course
        course = Course(
            name="Test Course",
            slug="test-course",
            semester="2024_WiSe",
            university_id=university.id,
        )
        db.session.add(course)
        db.session.flush()

        # Create student
        student = Student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Informatik",
        )
        db.session.add(student)
        db.session.flush()

        # Create enrollment
        enrollment = Enrollment(
            student_id=student.id,
            course_id=course.id,
            status="active",
        )
        db.session.add(enrollment)
        db.session.commit()

        return {
            "university_id": university.id,
            "course_id": course.id,
            "student_id": student.id,
            "enrollment_id": enrollment.id,
        }


class TestDocumentIndexRoute:
    """Tests for document listing route."""

    def test_index_empty(self, client, app):
        """Test document list with no documents."""
        with app.app_context():
            response = client.get("/documents/")
            assert response.status_code == 200
            assert b"Dokumente" in response.data
            assert b"Keine Dokumente gefunden" in response.data

    def test_index_page_loads(self, client, sample_data, app):
        """Test document list page loads correctly."""
        with app.app_context():
            response = client.get("/documents/")
            assert response.status_code == 200
            assert b"Dokumente" in response.data


class TestDocumentUploadRoute:
    """Tests for document upload route."""

    def test_upload_get(self, client, sample_data, app):
        """Test upload form page."""
        with app.app_context():
            response = client.get("/documents/upload")
            assert response.status_code == 200
            assert b"Dokument hochladen" in response.data
            assert b"Datei" in response.data

    def test_upload_post_no_file(self, client, sample_data, app):
        """Test upload with no file selected."""
        with app.app_context():
            response = client.post(
                "/documents/upload",
                data={
                    "enrollment_id": sample_data["enrollment_id"],
                    "submission_type": "document",
                },
            )
            assert response.status_code == 200
            # Should show error about missing file
            assert b"Datei" in response.data

    def test_upload_post_invalid_type(self, client, sample_data, app):
        """Test upload with invalid file type."""
        with app.app_context():
            data = {
                "file": (io.BytesIO(b"test content"), "test.exe"),
                "enrollment_id": sample_data["enrollment_id"],
                "submission_type": "document",
            }
            response = client.post(
                "/documents/upload",
                data=data,
                content_type="multipart/form-data",
            )
            # Should reject .exe files
            assert response.status_code == 200


class TestBulkUploadRoute:
    """Tests for bulk upload route."""

    def test_bulk_upload_get(self, client, sample_data, app):
        """Test bulk upload form page."""
        with app.app_context():
            response = client.get("/documents/bulk-upload")
            assert response.status_code == 200
            assert b"Bulk-Upload" in response.data


class TestSubmissionsRoute:
    """Tests for submissions listing route."""

    def test_submissions_empty(self, client, app):
        """Test submissions list with no submissions."""
        with app.app_context():
            response = client.get("/documents/submissions")
            assert response.status_code == 200
            assert b"Einreichungen" in response.data
            assert b"Keine Einreichungen gefunden" in response.data

    def test_submissions_page_loads(self, client, sample_data, app):
        """Test submissions list page loads correctly."""
        with app.app_context():
            response = client.get("/documents/submissions")
            assert response.status_code == 200
            assert b"Einreichungen" in response.data


class TestEmailImportRoute:
    """Tests for email import route."""

    def test_email_import_get(self, client, sample_data, app):
        """Test email import form page."""
        with app.app_context():
            response = client.get("/documents/email-import")
            assert response.status_code == 200
            assert b"E-Mail-Import" in response.data
            assert b"E-Mail-Datei" in response.data

    def test_email_import_no_file(self, client, sample_data, app):
        """Test email import with no file."""
        with app.app_context():
            response = client.post(
                "/documents/email-import",
                data={},
            )
            assert response.status_code == 200
            # Should show error about missing file
            assert b"Datei" in response.data


class TestDocumentShowRoute:
    """Tests for document detail route."""

    def test_show_not_found(self, client, app):
        """Test showing non-existent document."""
        with app.app_context():
            response = client.get("/documents/999")
            # Should redirect to index
            assert response.status_code == 302


class TestDocumentDeleteRoute:
    """Tests for document deletion route."""

    def test_delete_not_found(self, client, app):
        """Test deleting non-existent document."""
        with app.app_context():
            response = client.get("/documents/999/delete")
            # Should redirect to index
            assert response.status_code == 302
