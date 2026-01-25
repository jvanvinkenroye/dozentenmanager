"""
Integration tests for exam routes.

This module tests the Flask web interface for exam management.
"""

from datetime import date

import pytest

from app.services.course_service import CourseService
from app.services.exam_service import ExamService
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
def exam_service():
    """Return an ExamService instance."""
    return ExamService()


class TestExamListRoute:
    """Test exam list route."""

    def test_list_exams_empty(self, app, auth_client, university_service, course_service):
        """Test listing exams when none exist."""
        response = auth_client.get("/exams/")
        assert response.status_code == 200
        assert "Keine Prüfungen gefunden" in response.data.decode("utf-8")

    def test_list_exams_with_data(
        self, app, auth_client, university_service, course_service, exam_service
    ):
        """Test listing exams with existing data."""
        # Create test data
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        exam_service.add_exam(
            name="Midterm Exam",
            course_id=course.id,
            exam_date=date(2024, 6, 15),
            max_points=100.0,
        )

        response = auth_client.get("/exams/")
        assert response.status_code == 200
        assert "Midterm Exam" in response.data.decode("utf-8")

    def test_list_exams_filter_by_course(
        self, app, auth_client, university_service, course_service, exam_service
    ):
        """Test filtering exams by course."""
        # Create test data
        university = university_service.add_university("TH Köln")
        course1 = course_service.add_course(
            name="Programming I",
            semester="2024_WiSe",
            university_id=university.id,
        )
        course2 = course_service.add_course(
            name="Programming II",
            semester="2024_SoSe",
            university_id=university.id,
        )
        exam_service.add_exam("Exam 1", course1.id, date(2024, 6, 15), 100.0)
        exam_service.add_exam("Exam 2", course2.id, date(2024, 7, 20), 100.0)

        course1_id = course1.id

        response = auth_client.get(f"/exams/?course_id={course1_id}")
        assert response.status_code == 200
        assert "Exam 1" in response.data.decode("utf-8")
        assert "Exam 2" not in response.data.decode("utf-8")


class TestExamShowRoute:
    """Test exam detail route."""

    def test_show_exam_success(self, app, auth_client, university_service, course_service, exam_service):
        """Test showing exam details."""
        # Create test data
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        exam = exam_service.add_exam(
            name="Final Exam",
            course_id=course.id,
            exam_date=date(2024, 7, 15),
            max_points=120.0,
            weight=60.0,
            description="Written final exam",
        )
        exam_id = exam.id

        response = auth_client.get(f"/exams/{exam_id}")
        assert response.status_code == 200
        response_text = response.data.decode("utf-8")
        assert "Final Exam" in response_text
        assert "120.0" in response_text
        assert "60.0" in response_text
        assert "Written final exam" in response_text

    def test_show_exam_not_found(self, app, auth_client, university_service, course_service):
        """Test showing non-existent exam."""
        response = auth_client.get("/exams/99999")
        assert response.status_code == 302  # Redirect to list


class TestExamNewRoute:
    """Test exam creation route."""

    def test_new_exam_get(self, app, auth_client, university_service, course_service):
        """Test GET request to new exam form."""
        response = auth_client.get("/exams/new")
        assert response.status_code == 200
        assert "Neue Prüfung" in response.data.decode("utf-8")

    def test_new_exam_post_success(
        self, app, auth_client, university_service, course_service
    ):
        """Test successful exam creation."""
        # Create test data
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        course_id = course.id

        response = auth_client.post(
            "/exams/new",
            data={
                "name": "Midterm Exam",
                "course_id": str(course_id),
                "exam_date": "2024-06-15",
                "max_points": "100",
                "weight": "50",
                "description": "Test description",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        response_text = response.data.decode("utf-8")
        # Check that we're on the detail page showing the created exam
        assert "Midterm Exam" in response_text
        assert "Prüfungsdetails" in response_text

    def test_new_exam_missing_name(
        self, app, auth_client, university_service, course_service
    ):
        """Test exam creation with missing name."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        course_id = course.id

        response = auth_client.post(
            "/exams/new",
            data={
                "course_id": str(course_id),
                "exam_date": "2024-06-15",
                "max_points": "100",
            },
        )

        assert response.status_code == 200
        assert "required" in response.data.decode("utf-8").lower()

    def test_new_exam_missing_course(
        self, app, auth_client, university_service, course_service
    ):
        """Test exam creation with missing course."""
        response = auth_client.post(
            "/exams/new",
            data={
                "name": "Test Exam",
                "exam_date": "2024-06-15",
                "max_points": "100",
            },
        )

        assert response.status_code == 200
        assert "required" in response.data.decode("utf-8").lower()

    def test_new_exam_missing_date(
        self, app, auth_client, university_service, course_service
    ):
        """Test exam creation with missing date."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        course_id = course.id

        response = auth_client.post(
            "/exams/new",
            data={
                "name": "Test Exam",
                "course_id": str(course_id),
                "max_points": "100",
            },
        )

        assert response.status_code == 200
        assert "required" in response.data.decode("utf-8").lower()

    def test_new_exam_missing_max_points(
        self, app, auth_client, university_service, course_service
    ):
        """Test exam creation with missing max points."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        course_id = course.id

        response = auth_client.post(
            "/exams/new",
            data={
                "name": "Test Exam",
                "course_id": str(course_id),
                "exam_date": "2024-06-15",
            },
        )

        assert response.status_code == 200
        assert "required" in response.data.decode("utf-8").lower()

    def test_new_exam_invalid_max_points(
        self, app, auth_client, university_service, course_service
    ):
        """Test exam creation with invalid max points."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        course_id = course.id

        response = auth_client.post(
            "/exams/new",
            data={
                "name": "Test Exam",
                "course_id": str(course_id),
                "exam_date": "2024-06-15",
                "max_points": "0",
            },
        )

        assert response.status_code == 200
        assert "greater than 0" in response.data.decode("utf-8")

    def test_new_exam_invalid_weight(
        self, app, auth_client, university_service, course_service
    ):
        """Test exam creation with invalid weight."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        course_id = course.id

        response = auth_client.post(
            "/exams/new",
            data={
                "name": "Test Exam",
                "course_id": str(course_id),
                "exam_date": "2024-06-15",
                "max_points": "100",
                "weight": "150",
            },
        )

        assert response.status_code == 200
        assert "between 0 and 100" in response.data.decode("utf-8")


class TestExamEditRoute:
    """Test exam edit route."""

    def test_edit_exam_get(self, app, auth_client, university_service, course_service, exam_service):
        """Test GET request to edit exam form."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        exam = exam_service.add_exam("Test Exam", course.id, date(2024, 6, 15), 100.0)
        exam_id = exam.id

        response = auth_client.get(f"/exams/{exam_id}/edit")
        assert response.status_code == 200
        assert "bearbeiten" in response.data.decode("utf-8").lower()
        assert "Test Exam" in response.data.decode("utf-8")

    def test_edit_exam_post_success(
        self, app, auth_client, university_service, course_service, exam_service
    ):
        """Test successful exam update."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        exam = exam_service.add_exam("Original Name", course.id, date(2024, 6, 15), 100.0)
        exam_id = exam.id
        course_id = course.id

        response = auth_client.post(
            f"/exams/{exam_id}/edit",
            data={
                "name": "Updated Name",
                "course_id": str(course_id),
                "exam_date": "2024-07-20",
                "max_points": "120",
                "weight": "75",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        response_text = response.data.decode("utf-8")
        # Check that we're on the detail page with updated info
        assert "Updated Name" in response_text
        assert "Prüfungsdetails" in response_text

    def test_edit_exam_not_found(self, app, auth_client, university_service, course_service):
        """Test editing non-existent exam."""
        response = auth_client.get("/exams/99999/edit")
        assert response.status_code == 302  # Redirect


class TestExamDeleteRoute:
    """Test exam delete route."""

    def test_delete_exam_get(self, app, auth_client, university_service, course_service, exam_service):
        """Test GET request to delete confirmation page."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        exam = exam_service.add_exam("Test Exam", course.id, date(2024, 6, 15), 100.0)
        exam_id = exam.id

        response = auth_client.get(f"/exams/{exam_id}/delete")
        assert response.status_code == 200
        response_text = response.data.decode("utf-8")
        assert "löschen" in response_text.lower()
        assert "Test Exam" in response_text

    def test_delete_exam_post_success(
        self, app, auth_client, university_service, course_service, exam_service
    ):
        """Test successful exam deletion."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        exam = exam_service.add_exam("Test Exam", course.id, date(2024, 6, 15), 100.0)
        exam_id = exam.id

        response = auth_client.post(f"/exams/{exam_id}/delete", follow_redirects=True)

        assert response.status_code == 200
        response_text = response.data.decode("utf-8")
        # Check that we're redirected back to the exam list
        assert "Prüfungen" in response_text

    def test_delete_exam_not_found(
        self, app, auth_client, university_service, course_service
    ):
        """Test deleting non-existent exam."""
        response = auth_client.get("/exams/99999/delete")
        assert response.status_code == 302  # Redirect
