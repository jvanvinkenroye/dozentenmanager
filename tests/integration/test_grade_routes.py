"""
Integration tests for grade routes.

Tests the grade management web interface including listing, adding,
updating, and deleting grades, as well as the dashboard and statistics.
"""

import pytest

from app import db
from app.models import (
    Course,
    Enrollment,
    Exam,
    ExamComponent,
    Grade,
    Student,
    University,
)


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
            email="max@test.com",
            student_id="12345678",
            program="Computer Science",
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
        db.session.flush()

        # Create exam
        from datetime import date

        exam = Exam(
            name="Test Exam",
            course_id=course.id,
            exam_date=date(2024, 1, 15),
            max_points=100,
            weight=100,
        )
        db.session.add(exam)
        db.session.flush()

        db.session.commit()

        yield {
            "university": university,
            "course": course,
            "student": student,
            "enrollment": enrollment,
            "exam": exam,
        }


class TestGradeIndexRoute:
    """Tests for grade list route."""

    def test_index_empty(self, client):
        """Test empty grade list."""
        response = client.get("/grades/")
        assert response.status_code == 200
        assert b"Noten" in response.data

    def test_index_with_grades(self, client, sample_data):
        """Test grade list with data."""
        # Add a grade
        grade = Grade(
            enrollment_id=sample_data["enrollment"].id,
            exam_id=sample_data["exam"].id,
            points=80,
            percentage=80.0,
            grade_value=2.0,
            grade_label="gut",
            is_final=True,
        )
        db.session.add(grade)
        db.session.commit()

        response = client.get("/grades/")
        assert response.status_code == 200
        assert b"Mustermann" in response.data
        assert b"80" in response.data


class TestGradeNewRoute:
    """Tests for new grade route."""

    def test_new_get(self, client, sample_data):
        """Test new grade form page."""
        response = client.get("/grades/new")
        assert response.status_code == 200
        assert b"Neue Note" in response.data


class TestGradeDashboardRoute:
    """Tests for grade dashboard route."""

    def test_dashboard_empty(self, client):
        """Test dashboard with no grades."""
        response = client.get("/grades/dashboard")
        assert response.status_code == 200
        assert b"Noten-Dashboard" in response.data

    def test_dashboard_with_data(self, client, sample_data):
        """Test dashboard with grades."""
        # Add some grades
        grade = Grade(
            enrollment_id=sample_data["enrollment"].id,
            exam_id=sample_data["exam"].id,
            points=85,
            percentage=85.0,
            grade_value=1.7,
            grade_label="gut",
            is_final=True,
        )
        db.session.add(grade)
        db.session.commit()

        response = client.get("/grades/dashboard")
        assert response.status_code == 200
        assert b"Gesamt Noten" in response.data


class TestGradeExamStatsRoute:
    """Tests for exam statistics route."""

    def test_exam_stats_no_grades(self, client, sample_data):
        """Test exam stats page with no grades."""
        response = client.get(f"/grades/exam/{sample_data['exam'].id}/stats")
        assert response.status_code == 200
        assert b"Test Exam" in response.data

    def test_exam_stats_with_grades(self, client, sample_data):
        """Test exam stats page with grades."""
        grade = Grade(
            enrollment_id=sample_data["enrollment"].id,
            exam_id=sample_data["exam"].id,
            points=75,
            percentage=75.0,
            grade_value=2.3,
            grade_label="gut",
            is_final=False,
        )
        db.session.add(grade)
        db.session.commit()

        response = client.get(f"/grades/exam/{sample_data['exam'].id}/stats")
        assert response.status_code == 200


class TestGradeStudentGradesRoute:
    """Tests for student grades route."""

    def test_student_grades(self, client, sample_data):
        """Test student grades page."""
        response = client.get(f"/grades/student/{sample_data['student'].id}")
        assert response.status_code == 200
        assert b"Mustermann" in response.data


class TestGradeComponentsRoute:
    """Tests for exam components route."""

    def test_components_empty(self, client, sample_data):
        """Test components page with no components."""
        response = client.get(f"/grades/components/{sample_data['exam'].id}")
        assert response.status_code == 200
        assert "Prüfungskomponenten".encode() in response.data

    def test_components_with_data(self, client, sample_data):
        """Test components page with components."""
        component = ExamComponent(
            exam_id=sample_data["exam"].id,
            name="Written Test",
            weight=60.0,
            max_points=60,
            order=1,
        )
        db.session.add(component)
        db.session.commit()

        response = client.get(f"/grades/components/{sample_data['exam'].id}")
        assert response.status_code == 200
        assert b"Written Test" in response.data
        assert b"60%" in response.data


class TestGradeNewComponentRoute:
    """Tests for new component route."""

    def test_new_component_get(self, client, sample_data):
        """Test new component form page."""
        response = client.get(f"/grades/components/{sample_data['exam'].id}/new")
        assert response.status_code == 200
        assert "Neue Prüfungskomponente".encode() in response.data


class TestGradeBulkRoute:
    """Tests for bulk grading route."""

    def test_bulk_get_no_exam(self, client):
        """Test bulk grading page without exam selected."""
        response = client.get("/grades/bulk")
        assert response.status_code == 200
        assert b"Sammelbenotung" in response.data

    def test_bulk_get_with_exam(self, client, sample_data):
        """Test bulk grading page with exam selected."""
        response = client.get(f"/grades/bulk?exam_id={sample_data['exam'].id}")
        assert response.status_code == 200
        assert b"Sammelbenotung" in response.data


class TestGradeApiRoutes:
    """Tests for API routes."""

    def test_api_exam_components_empty(self, client, sample_data):
        """Test API for exam components when empty."""
        response = client.get(f"/grades/api/exam/{sample_data['exam'].id}/components")
        assert response.status_code == 200
        data = response.get_json()
        assert "components" in data
        assert len(data["components"]) == 0

    def test_api_exam_components_with_data(self, client, sample_data):
        """Test API for exam components with data."""
        component = ExamComponent(
            exam_id=sample_data["exam"].id,
            name="Part 1",
            weight=50.0,
            max_points=50,
        )
        db.session.add(component)
        db.session.commit()

        response = client.get(f"/grades/api/exam/{sample_data['exam'].id}/components")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["components"]) == 1
        assert data["components"][0]["name"] == "Part 1"

    def test_api_calculate_grade(self, client):
        """Test grade calculation API."""
        response = client.post(
            "/grades/api/calculate",
            json={"points": 85, "max_points": 100},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["percentage"] == 85.0
        assert data["grade_value"] == 1.7
        assert data["is_passing"]


class TestGradeShowRoute:
    """Tests for grade detail route."""

    def test_show_not_found(self, client):
        """Test grade detail for non-existent grade."""
        response = client.get("/grades/999")
        assert response.status_code == 404

    def test_show_existing(self, client, sample_data):
        """Test grade detail for existing grade."""
        grade = Grade(
            enrollment_id=sample_data["enrollment"].id,
            exam_id=sample_data["exam"].id,
            points=90,
            percentage=90.0,
            grade_value=1.3,
            grade_label="sehr gut",
            is_final=True,
        )
        db.session.add(grade)
        db.session.commit()

        response = client.get(f"/grades/{grade.id}")
        assert response.status_code == 200
        assert b"Note Details" in response.data
        assert b"90" in response.data


class TestGradeDeleteRoute:
    """Tests for grade delete route."""

    def test_delete_not_found(self, client):
        """Test delete for non-existent grade."""
        response = client.get("/grades/999/delete")
        assert response.status_code == 404

    def test_delete_get(self, client, sample_data):
        """Test delete confirmation page."""
        grade = Grade(
            enrollment_id=sample_data["enrollment"].id,
            exam_id=sample_data["exam"].id,
            points=70,
            percentage=70.0,
            grade_value=2.7,
            grade_label="befriedigend",
        )
        db.session.add(grade)
        db.session.commit()

        response = client.get(f"/grades/{grade.id}/delete")
        assert response.status_code == 200
        assert "Note löschen".encode() in response.data
