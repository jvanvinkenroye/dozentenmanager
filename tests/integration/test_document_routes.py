"""
Integration tests for document routes.

This module tests the document management web routes including
document upload, listing, and deletion functionality.
"""

import io
import shutil
from email.message import EmailMessage
from pathlib import Path

import pytest

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


class TestEmailImportPost:
    """Tests for the email import POST handler with real email files."""

    @pytest.fixture(autouse=True)
    def _cleanup_uploads(self):
        """Remove attachment files created under uploads/ by the import."""
        yield
        shutil.rmtree(Path("uploads") / "test-uni", ignore_errors=True)

    def _build_eml(
        self,
        sender="Max Mustermann <max@example.com>",
        subject="Abgabe Hausarbeit",
        attachment_name="hausarbeit.pdf",
    ):
        """Build a raw .eml file with a PDF attachment."""
        message = EmailMessage()
        message["From"] = sender
        message["To"] = "dozent@example.com"
        message["Subject"] = subject
        message["Date"] = "Mon, 20 Jan 2025 10:00:00 +0100"
        message.set_content("Anbei meine Abgabe.")
        message.add_attachment(
            b"%PDF-1.4 test content",
            maintype="application",
            subtype="pdf",
            filename=attachment_name,
        )
        return message.as_bytes()

    def test_import_eml_matches_student(self, auth_client, sample_data, app):
        """An .eml from an enrolled student's address creates a document."""
        response = auth_client.post(
            "/documents/email-import",
            data={
                "file": (io.BytesIO(self._build_eml()), "mail.eml"),
                "course_id": "",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        page = response.data.decode("utf-8")
        assert "Import" in page

        documents = db.session.query(Document).all()
        assert len(documents) == 1
        assert documents[0].original_filename == "hausarbeit.pdf"

        submissions = db.session.query(Submission).all()
        assert len(submissions) == 1
        assert submissions[0].enrollment_id == sample_data["enrollment_id"]
        assert submissions[0].submission_type == "email_attachment"

    def test_import_eml_with_course_filter(self, auth_client, sample_data, app):
        """Passing a course_id still matches students of that course."""
        response = auth_client.post(
            "/documents/email-import",
            data={
                "file": (io.BytesIO(self._build_eml()), "mail.eml"),
                "course_id": str(sample_data["course_id"]),
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert db.session.query(Document).count() == 1

    def test_import_eml_unmatched_sender(self, auth_client, sample_data, app):
        """An email from an unknown address creates no document."""
        eml = self._build_eml(sender="Unknown Person <nobody@example.com>")
        response = auth_client.post(
            "/documents/email-import",
            data={
                "file": (io.BytesIO(eml), "mail.eml"),
                "course_id": "",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert db.session.query(Document).count() == 0

    def test_import_mbox_with_multiple_messages(self, auth_client, sample_data, app):
        """An .mbox file with several messages imports each of them."""
        eml_bytes = self._build_eml()
        mbox_content = b""
        for _ in range(2):
            mbox_content += b"From max@example.com Mon Jan 20 10:00:00 2025\n"
            mbox_content += eml_bytes.replace(b"\r\n", b"\n") + b"\n\n"

        response = auth_client.post(
            "/documents/email-import",
            data={
                "file": (io.BytesIO(mbox_content), "mails.mbox"),
                "course_id": "",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert db.session.query(Document).count() == 2

    def test_import_rejects_wrong_extension(self, auth_client, sample_data, app):
        """Files that are not .eml/.mbox are rejected by the form."""
        response = auth_client.post(
            "/documents/email-import",
            data={
                "file": (io.BytesIO(b"plain text"), "mail.txt"),
                "course_id": "",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert "Erlaubte Dateitypen" in response.data.decode("utf-8")
        assert db.session.query(Document).count() == 0

    def test_import_requires_login(self, client, sample_data, app):
        """Anonymous users are redirected to login."""
        response = client.get("/documents/email-import")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]
