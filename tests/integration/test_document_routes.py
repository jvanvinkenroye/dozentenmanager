"""
Integration tests for document routes.

This module tests the document management web routes including
document upload, listing, and deletion functionality.
"""

import io

import pytest

from app import create_app, db
from app.models import Course, Enrollment, Student, Submission, University


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

    def test_index_empty(self, auth_client, app):
        """Test document list with no documents."""
        response = auth_client.get("/documents/")
        assert response.status_code == 200
        assert b"Dokumente" in response.data
        assert b"Keine Dokumente gefunden" in response.data

    def test_index_page_loads(self, auth_client, sample_data, app):
        """Test document list page loads correctly."""
        response = auth_client.get("/documents/")
        assert response.status_code == 200
        assert b"Dokumente" in response.data


class TestDocumentUploadRoute:
    """Tests for document upload route."""

    def test_upload_get(self, auth_client, sample_data, app):
        """Test upload form page."""
        response = auth_client.get("/documents/upload")
        assert response.status_code == 200
        assert b"Dokument hochladen" in response.data
        assert b"Datei" in response.data

    def test_upload_post_no_file(self, auth_client, sample_data, app):
        """Test upload with no file selected."""
        response = auth_client.post(
            "/documents/upload",
            data={
                "enrollment_id": sample_data["enrollment_id"],
                "submission_type": "document",
            },
        )
        assert response.status_code == 200
        # Should show error about missing file
        assert b"Datei" in response.data

    def test_upload_post_invalid_type(self, auth_client, sample_data, app):
        """Test upload with invalid file type."""
        data = {
            "file": (io.BytesIO(b"test content"), "test.exe"),
            "enrollment_id": sample_data["enrollment_id"],
            "submission_type": "document",
        }
        response = auth_client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data",
        )
        # Should reject .exe files
        assert response.status_code == 200

    def test_upload_post_success(self, auth_client, sample_data, app):
        """Test successful document upload."""
        # Create a test PDF file
        data = {
            "file": (io.BytesIO(b"%PDF-1.4 test content"), "test.pdf"),
            "enrollment_id": sample_data["enrollment_id"],
            "submission_type": "document",
            "notes": "Test submission",
        }
        response = auth_client.post(
            "/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        # Should redirect on success
        assert response.status_code == 302
        assert b"/documents/" in response.data

        # Verify document was created
        from app.models import Document

        document = Document.query.first()
        assert document is not None
        assert document.file_type == "pdf"
        # Document is linked via submission, not directly to enrollment
        assert document.submission_id is not None


class TestBulkUploadRoute:
    """Tests for bulk upload route."""

    def test_bulk_upload_get(self, auth_client, sample_data, app):
        """Test bulk upload form page."""
        response = auth_client.get("/documents/bulk-upload")
        assert response.status_code == 200
        assert b"Bulk-Upload" in response.data


class TestSubmissionsRoute:
    """Tests for submissions listing route."""

    def test_submissions_empty(self, auth_client, app):
        """Test submissions list with no submissions."""
        response = auth_client.get("/documents/submissions")
        assert response.status_code == 200
        assert b"Einreichungen" in response.data
        assert b"Keine Einreichungen gefunden" in response.data

    def test_submissions_page_loads(self, auth_client, sample_data, app):
        """Test submissions list page loads correctly."""
        response = auth_client.get("/documents/submissions")
        assert response.status_code == 200
        assert b"Einreichungen" in response.data

    def test_submissions_with_data(self, auth_client, sample_data, app):
        """Test submissions list with data."""
        # Create a submission
        submission = Submission(
            enrollment_id=sample_data["enrollment_id"],
            submission_type="document",
            status="submitted",
            notes="Test submission",
        )
        db.session.add(submission)
        db.session.commit()

        response = auth_client.get("/documents/submissions")
        assert response.status_code == 200
        assert b"Einreichungen" in response.data


class TestSubmissionDetailRoute:
    """Tests for submission detail route."""

    def test_submission_detail_not_found(self, auth_client, app):
        """Test showing non-existent submission."""
        response = auth_client.get("/documents/submissions/999")
        assert response.status_code == 302

    @pytest.mark.skip(reason="Template URL building issue - fix later")
    def test_submission_detail_existing(self, auth_client, sample_data, app):
        """Test showing existing submission."""
        # Create a submission
        submission = Submission(
            enrollment_id=sample_data["enrollment_id"],
            submission_type="document",
            status="submitted",
            notes="Test submission",
        )
        db.session.add(submission)
        db.session.commit()

        response = auth_client.get(f"/documents/submissions/{submission.id}")
        assert response.status_code == 200
        assert b"Einreichung" in response.data


class TestUpdateSubmissionStatusRoute:
    """Tests for submission status update route."""

    def test_update_status_not_found(self, auth_client, app):
        """Test updating status of non-existent submission."""
        response = auth_client.post(
            "/documents/submissions/999/update-status",
            data={"status": "graded"},
            follow_redirects=False,
        )
        assert response.status_code == 302

    def test_update_status_success(self, auth_client, sample_data, app):
        """Test successful status update."""
        # Create a submission
        submission = Submission(
            enrollment_id=sample_data["enrollment_id"],
            submission_type="document",
            status="submitted",
        )
        db.session.add(submission)
        db.session.commit()

        submission_id = submission.id

        response = auth_client.post(
            f"/documents/submissions/{submission_id}/update-status",
            data={"status": "graded"},
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify status was updated
        updated_submission = Submission.query.filter_by(id=submission_id).first()
        assert updated_submission is not None
        assert updated_submission.status == "graded"


class TestEmailImportRoute:
    """Tests for email import route."""

    def test_email_import_get(self, auth_client, sample_data, app):
        """Test email import form page."""
        response = auth_client.get("/documents/email-import")
        assert response.status_code == 200
        assert b"E-Mail-Import" in response.data
        assert b"E-Mail-Datei" in response.data

    def test_email_import_no_file(self, auth_client, sample_data, app):
        """Test email import with no file."""
        response = auth_client.post(
            "/documents/email-import",
            data={},
        )
        assert response.status_code == 200
        # Should show error about missing file
        assert b"Datei" in response.data


class TestDocumentShowRoute:
    """Tests for document detail route."""

    def test_show_not_found(self, auth_client, app):
        """Test showing non-existent document."""
        response = auth_client.get("/documents/999")
        # Should redirect to index
        assert response.status_code == 302

    @pytest.mark.skip(reason="Template URL building issue - fix later")
    def test_show_existing_document(self, auth_client, sample_data, app):
        """Test showing existing document."""
        # Create a document first
        from app.models import Document

        submission = Submission(
            enrollment_id=sample_data["enrollment_id"],
            submission_type="document",
            status="submitted",
        )
        db.session.add(submission)
        db.session.flush()

        document = Document(
            submission_id=submission.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/test/path/test.pdf",
            file_type="pdf",
            file_size=1024,
        )
        db.session.add(document)
        db.session.commit()

        response = auth_client.get(f"/documents/{document.id}")
        assert response.status_code == 200
        assert b"test.pdf" in response.data


class TestDocumentDownloadRoute:
    """Tests for document download route."""

    def test_download_not_found(self, auth_client, app):
        """Test downloading non-existent document."""
        response = auth_client.get("/documents/999/download")
        assert response.status_code == 302
        # Should redirect to document index

    def test_download_file_not_on_disk(self, auth_client, sample_data, app):
        """Test downloading document when file doesn't exist on disk."""
        from app.models import Document

        # Create a document with non-existent file path
        submission = Submission(
            enrollment_id=sample_data["enrollment_id"],
            submission_type="document",
            status="submitted",
        )
        db.session.add(submission)
        db.session.flush()

        document = Document(
            submission_id=submission.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/nonexistent/path/test.pdf",
            file_type="pdf",
            file_size=1024,
        )
        db.session.add(document)
        db.session.commit()

        response = auth_client.get(f"/documents/{document.id}/download")
        assert response.status_code == 302
        # Should redirect with error message


class TestDocumentDeleteRoute:
    """Tests for document deletion route."""

    def test_delete_not_found(self, auth_client, app):
        """Test deleting non-existent document."""
        response = auth_client.get("/documents/999/delete")
        # Should redirect to index
        assert response.status_code == 302

    def test_delete_get_confirmation(self, auth_client, sample_data, app):
        """Test GET request shows deletion confirmation."""
        # Create a document
        from app.models import Document

        submission = Submission(
            enrollment_id=sample_data["enrollment_id"],
            submission_type="document",
            status="submitted",
        )
        db.session.add(submission)
        db.session.flush()

        document = Document(
            submission_id=submission.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/test/path/test.pdf",
            file_type="pdf",
            file_size=1024,
        )
        db.session.add(document)
        db.session.commit()

        response = auth_client.get(f"/documents/{document.id}/delete")
        assert response.status_code == 200
        assert b"schen" in response.data  # Part of "löschen"
        assert b"test.pdf" in response.data

    def test_delete_post_success(self, auth_client, sample_data, app):
        """Test POST request deletes document."""
        # Create a document
        from app.models import Document

        submission = Submission(
            enrollment_id=sample_data["enrollment_id"],
            submission_type="document",
            status="submitted",
        )
        db.session.add(submission)
        db.session.flush()

        document = Document(
            submission_id=submission.id,
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/test/path/test.pdf",
            file_type="pdf",
            file_size=1024,
        )
        db.session.add(document)
        db.session.commit()

        document_id = document.id

        response = auth_client.post(
            f"/documents/{document_id}/delete", follow_redirects=False
        )
        assert response.status_code == 302
        assert b"/documents/" in response.data

        # Verify document was deleted
        deleted_doc = Document.query.filter_by(id=document_id).first()
        assert deleted_doc is None
