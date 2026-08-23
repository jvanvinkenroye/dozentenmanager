"""
Integration tests for the JSON API routes.

This module tests the read-only REST endpoints under /api.
"""

from datetime import date

import pytest

from app import db
from app.models import Course, Enrollment, Exam, Student, University
from app.services.grade_service import GradeService


@pytest.fixture
def api_data(app):
    """Create a university, course, student, enrollment, exam and grade."""
    university = University(name="Test Uni", slug="test-uni")
    db.session.add(university)
    db.session.flush()

    course = Course(
        name="Statistik",
        slug="statistik",
        semester="2024_WiSe",
        university_id=university.id,
    )
    db.session.add(course)
    db.session.flush()

    student = Student(
        first_name="Max",
        last_name="Mustermann",
        student_id="12345678",
        email="max@example.com",
        program="Informatik",
    )
    db.session.add(student)
    db.session.flush()

    enrollment = Enrollment(
        student_id=student.id, course_id=course.id, status="active"
    )
    db.session.add(enrollment)

    exam = Exam(
        name="Klausur",
        course_id=course.id,
        exam_date=date.today(),
        max_points=100.0,
        weight=100.0,
    )
    db.session.add(exam)
    db.session.commit()

    grade = GradeService().add_grade(
        enrollment_id=enrollment.id, exam_id=exam.id, points=90.0, is_final=True
    )

    return {
        "university": university,
        "course": course,
        "student": student,
        "enrollment": enrollment,
        "exam": exam,
        "grade": grade,
    }


class TestStudentApi:
    """Tests for /api/students."""

    def test_list_students(self, auth_client, api_data):
        response = auth_client.get("/api/students")
        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload) == 1
        assert payload[0]["student_id"] == "12345678"

    def test_list_students_with_filters(self, auth_client, api_data):
        assert auth_client.get("/api/students?search=Mustermann").get_json()
        assert auth_client.get("/api/students?search=Nobody").get_json() == []
        assert auth_client.get("/api/students?program=Informatik").get_json()
        assert auth_client.get("/api/students?program=Jura").get_json() == []

    def test_get_student(self, auth_client, api_data):
        student_id = api_data["student"].id
        response = auth_client.get(f"/api/students/{student_id}")
        assert response.status_code == 200
        assert response.get_json()["email"] == "max@example.com"

    def test_get_student_not_found(self, auth_client, api_data):
        response = auth_client.get("/api/students/999")
        assert response.status_code == 404
        assert response.get_json()["error"] == "Student not found"

    def test_requires_login(self, client, api_data):
        response = client.get("/api/students")
        assert response.status_code == 302


class TestCourseApi:
    """Tests for /api/courses."""

    def test_list_courses(self, auth_client, api_data):
        response = auth_client.get("/api/courses")
        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload) == 1
        assert payload[0]["name"] == "Statistik"

    def test_list_courses_with_filters(self, auth_client, api_data):
        uni_id = api_data["university"].id
        assert auth_client.get(f"/api/courses?university_id={uni_id}").get_json()
        assert auth_client.get("/api/courses?university_id=999").get_json() == []
        assert auth_client.get("/api/courses?semester=2024_WiSe").get_json()
        assert auth_client.get("/api/courses?semester=1999_SoSe").get_json() == []

    def test_get_course(self, auth_client, api_data):
        course_id = api_data["course"].id
        response = auth_client.get(f"/api/courses/{course_id}")
        assert response.status_code == 200
        assert response.get_json()["semester"] == "2024_WiSe"

    def test_get_course_not_found(self, auth_client, api_data):
        response = auth_client.get("/api/courses/999")
        assert response.status_code == 404
        assert response.get_json()["error"] == "Course not found"


class TestGradeApi:
    """Tests for /api/grades."""

    def test_list_grades(self, auth_client, api_data):
        response = auth_client.get("/api/grades")
        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload) == 1
        assert payload[0]["points"] == 90.0

    def test_list_grades_with_filters(self, auth_client, api_data):
        enrollment_id = api_data["enrollment"].id
        exam_id = api_data["exam"].id
        course_id = api_data["course"].id

        assert auth_client.get(f"/api/grades?enrollment_id={enrollment_id}").get_json()
        assert auth_client.get(f"/api/grades?exam_id={exam_id}").get_json()
        assert auth_client.get(f"/api/grades?course_id={course_id}").get_json()
        assert auth_client.get("/api/grades?enrollment_id=999").get_json() == []

    def test_list_grades_is_final_filter(self, auth_client, api_data):
        assert auth_client.get("/api/grades?is_final=true").get_json()
        assert auth_client.get("/api/grades?is_final=false").get_json() == []
