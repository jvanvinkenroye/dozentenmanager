"""
Unit tests for DocumentService.
"""

import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from app.models.course import Course
from app.models.document import Document
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.submission import Submission
from app.models.university import University
from app.services.document_service import DocumentService


@pytest.fixture
def document_service(db):
    return DocumentService()


@pytest.fixture
def setup_data(db):
    # Create university
    uni = University(name="Test Uni", slug="test-uni")
    db.session.add(uni)
    db.session.flush()

    # Create student
    student = Student(
        first_name="Max",
        last_name="Mustermann",
        student_id="12345678",
        email="max@example.com",
        program="CS",
    )
    db.session.add(student)

    # Create course
    course = Course(
        name="Test Course",
        slug="test-course",
        semester="2023_SoSe",
        university_id=uni.id,
    )
    db.session.add(course)
    db.session.flush()

    # Create enrollment
    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        status="active",
        enrollment_date=datetime.now(UTC),
    )
    db.session.add(enrollment)
    db.session.commit()

    return {
        "uni": uni,
        "student": student,
        "course": course,
        "enrollment": enrollment,
    }


def test_get_upload_path(document_service, setup_data):
    enrollment = setup_data["enrollment"]
    filename = "test.pdf"

    with tempfile.TemporaryDirectory() as tmpdir:
        path = document_service.get_upload_path(enrollment, filename, base_path=tmpdir)
        
        expected_part = Path(tmpdir) / "test-uni" / "2023_SoSe" / "test-course" / "MustermannMax" / "test.pdf"
        assert Path(path) == expected_part


def test_get_upload_path_collision(document_service, setup_data):
    enrollment = setup_data["enrollment"]
    filename = "test.pdf"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create "existing" file
        full_path = Path(tmpdir) / "test-uni" / "2023_SoSe" / "test-course" / "MustermannMax" / "test.pdf"
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.touch()

        # Should generate _1
        path = document_service.get_upload_path(enrollment, filename, base_path=tmpdir)
        expected = full_path.parent / "test_1.pdf"
        assert Path(path) == expected


def test_create_submission(document_service, setup_data):
    enrollment = setup_data["enrollment"]
    
    submission = document_service.create_submission(
        enrollment_id=enrollment.id,
        submission_type="document",
        notes="Test submission"
    )

    assert submission.id is not None
    assert submission.enrollment_id == enrollment.id
    assert submission.status == "submitted"
    assert submission.notes == "Test submission"


def test_upload_document(document_service, setup_data, app):
    enrollment = setup_data["enrollment"]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Configure app to use temp dir for uploads
        app.config.update({"UPLOAD_FOLDER": str(Path(tmpdir) / "uploads")})
        
        # Create source file
        source_file = Path(tmpdir) / "source.pdf"
        source_file.write_text("dummy content")

        document = document_service.upload_document(
            file_path=str(source_file),
            enrollment_id=enrollment.id,
            submission_type="document"
        )

        assert document.id is not None
        assert document.filename == "source.pdf"
        assert document.file_size == 13  # "dummy content"
        assert Path(document.file_path).exists()
        assert Path(document.file_path).read_text() == "dummy content"
        
        # Verify it's in the correct structure
        expected_suffix = Path("test-uni") / "2023_SoSe" / "test-course" / "MustermannMax" / "source.pdf"
        assert str(document.file_path).endswith(str(expected_suffix))


def test_match_file_to_enrollment(document_service, setup_data):
    course = setup_data["course"]
    enrollment = setup_data["enrollment"]
    
    # Test LastnameFirstname match
    filename = "MustermannMax.pdf"
    matched = document_service.match_file_to_enrollment(filename, course.id)
    assert matched is not None
    assert matched.id == enrollment.id

    # Test FirstnameLastname match
    filename = "MaxMustermann.pdf"
    matched = document_service.match_file_to_enrollment(filename, course.id)
    assert matched is not None
    assert matched.id == enrollment.id
    
    # Test with separators
    filename = "Mustermann_Max_Hausarbeit.pdf"
    matched = document_service.match_file_to_enrollment(filename, course.id)
    assert matched is not None
    assert matched.id == enrollment.id

    # Test no match
    filename = "SchmidtHans.pdf"
    matched = document_service.match_file_to_enrollment(filename, course.id)
    assert matched is None


def test_update_submission_status(document_service, setup_data):
    enrollment = setup_data["enrollment"]
    submission = document_service.create_submission(enrollment.id)
    
    updated = document_service.update_submission_status(
        submission.id,
        status="graded",
        notes="Well done"
    )
    
    assert updated.status == "graded"
    assert updated.notes == "Well done"

    # Verify persistence
    fetched = document_service.get_submission(submission.id)
    assert fetched.status == "graded"


def test_delete_document(document_service, setup_data, app):
    enrollment = setup_data["enrollment"]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Configure app to use temp dir for uploads
        app.config.update({"UPLOAD_FOLDER": str(Path(tmpdir) / "uploads")})
        
        # Create dummy source file
        source_file = Path(tmpdir) / "source.pdf"
        source_file.write_text("content")

        doc = document_service.upload_document(
            file_path=str(source_file),
            enrollment_id=enrollment.id
        )
        
        doc_id = doc.id
        assert Path(doc.file_path).exists()

        result = document_service.delete_document(doc_id)
        assert result is True
        
        # Verify DB deletion
        with pytest.raises(ValueError):
            document_service.get_document(doc_id)
        
        # Verify file deletion
        assert not Path(doc.file_path).exists()
