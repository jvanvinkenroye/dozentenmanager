"""
Unit tests for Email Import CLI.
"""

import email
import tempfile
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.university import University
from cli.email_cli import (
    decode_email_header,
    extract_email_address,
    extract_student_id_from_text,
    import_emails,
    match_student_by_email,
    match_student_by_name,
    parse_eml_file,
    process_email_message,
)


@pytest.fixture
def setup_email_data(db):
    # Create university
    uni = University(name="Test Uni", slug="test-uni")
    db.session.add(uni)
    db.session.flush()

    # Create students
    student1 = Student(
        first_name="Max",
        last_name="Mustermann",
        student_id="12345678",
        email="max@example.com",
        program="CS",
    )
    student2 = Student(
        first_name="Maria",
        last_name="Musterfrau",
        student_id="87654321",
        email="maria@example.com",
        program="Math",
    )
    db.session.add(student1)
    db.session.add(student2)
    db.session.flush()

    # Create course
    course = Course(
        name="Test Course",
        slug="test-course",
        semester="2023_SoSe",
        university_id=uni.id,
    )
    db.session.add(course)
    db.session.flush()

    # Create enrollments
    enrollment1 = Enrollment(
        student_id=student1.id,
        course_id=course.id,
        status="active",
        enrollment_date=datetime.now(UTC),
    )
    enrollment2 = Enrollment(
        student_id=student2.id,
        course_id=course.id,
        status="active",
        enrollment_date=datetime.now(UTC),
    )
    db.session.add(enrollment1)
    db.session.add(enrollment2)
    db.session.commit()

    return {
        "student1": student1,
        "student2": student2,
        "course": course,
        "enrollment1": enrollment1,
    }


def test_decode_email_header():
    assert decode_email_header("Subject") == "Subject"
    assert decode_email_header("=?utf-8?b?VGVzdA==?=") == "Test"
    assert decode_email_header("=?iso-8859-1?q?M=FCller?=") == "Müller"


def test_extract_email_address():
    assert extract_email_address("test@example.com") == "test@example.com"
    assert extract_email_address("<test@example.com>") == "test@example.com"
    assert extract_email_address("Name <test@example.com>") == "test@example.com"
    assert extract_email_address('"Name" <test@example.com>') == "test@example.com"


def test_extract_student_id_from_text():
    assert extract_student_id_from_text("My ID is 12345678") == "12345678"
    assert extract_student_id_from_text("12345678") == "12345678"
    assert extract_student_id_from_text("No ID here") is None
    assert extract_student_id_from_text("123") is None  # Too short
    assert extract_student_id_from_text("123456789") is None  # Too long


def test_match_student_by_email(setup_email_data):
    # Match existing
    enrollment = match_student_by_email("max@example.com")
    assert enrollment is not None
    assert enrollment.student.first_name == "Max"

    # Match non-existing
    enrollment = match_student_by_email("unknown@example.com")
    assert enrollment is None


def test_match_student_by_name(setup_email_data):
    # Match First Last
    enrollment = match_student_by_name("Max Mustermann")
    assert enrollment is not None
    assert enrollment.student.id == setup_email_data["student1"].id

    # Match Last First
    enrollment = match_student_by_name("Mustermann Max")
    assert enrollment is not None
    assert enrollment.student.id == setup_email_data["student1"].id

    # Match Last, First
    enrollment = match_student_by_name("Mustermann, Max")
    assert enrollment is not None
    assert enrollment.student.id == setup_email_data["student1"].id
    
    # No match
    enrollment = match_student_by_name("Hans Schmidt")
    assert enrollment is None


def test_process_email_message(setup_email_data):
    msg = EmailMessage()
    msg["Subject"] = "Test Submission"
    msg["From"] = "max@example.com"
    msg.set_content("Here is my submission")

    result = process_email_message(msg)
    
    assert result["subject"] == "Test Submission"
    assert result["matched_student"] is not None
    assert result["matched_student"]["email"] == "max@example.com"


def test_process_email_message_match_by_id_in_subject(setup_email_data):
    msg = EmailMessage()
    msg["Subject"] = "Submission 12345678"
    msg["From"] = "private@gmail.com"  # Unknown email
    msg.set_content("Here is my submission")

    result = process_email_message(msg)
    
    assert result["matched_student"] is not None
    assert result["matched_student"]["id"] == setup_email_data["student1"].id


def test_parse_eml_file(setup_email_data):
    msg = EmailMessage()
    msg["Subject"] = "Test EML"
    msg["From"] = "max@example.com"
    msg.set_content("Content")
    
    with tempfile.NamedTemporaryFile(suffix=".eml", mode="wb") as tmp:
        tmp.write(msg.as_bytes())
        tmp.flush()
        
        results = parse_eml_file(tmp.name)
        
        assert len(results) == 1
        assert results[0]["subject"] == "Test EML"
        assert results[0]["matched_student"]["email"] == "max@example.com"


def test_import_emails(setup_email_data):
    msg = EmailMessage()
    msg["Subject"] = "Test Import"
    msg["From"] = "max@example.com"
    msg.set_content("Content")
    
    with tempfile.NamedTemporaryFile(suffix=".eml", mode="wb") as tmp:
        tmp.write(msg.as_bytes())
        tmp.flush()
        
        summary = import_emails(tmp.name)
        
        assert summary["files_processed"] == 1
        assert summary["emails_processed"] == 1
        assert summary["students_matched"] == 1