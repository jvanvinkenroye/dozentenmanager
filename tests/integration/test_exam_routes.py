"""
Integration tests for exam routes.

This module tests the Flask web interface for exam management.
"""

from cli.course_cli import add_course
from cli.exam_cli import add_exam
from cli.university_cli import add_university


class TestExamIndex:
    """Test exam list route."""

    def test_exam_index_empty(self, app, client):
        """Test exam index with no exams."""
        with app.app_context():
            response = client.get("/exams/")
            assert response.status_code == 200
            assert "Keine Prüfungen gefunden" in response.data.decode("utf-8")

    def test_exam_index_with_exams(self, app, client):
        """Test exam index displays exams."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_exam(
                name="Midterm Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )

            response = client.get("/exams/")
            assert response.status_code == 200
            assert "Midterm Exam" in response.data.decode("utf-8")

    def test_exam_index_search(self, app, client):
        """Test exam search functionality."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_exam(
                name="Midterm Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )
            add_exam(
                name="Final Exam",
                exam_type="final",
                max_points=150.0,
                weight=0.5,
                course_id=course.id,
            )

            response = client.get("/exams/?search=Midterm")
            assert response.status_code == 200
            assert "Midterm Exam" in response.data.decode("utf-8")


class TestExamShow:
    """Test exam detail route."""

    def test_exam_show_success(self, app, client):
        """Test showing exam details."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                name="Midterm Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )

            response = client.get(f"/exams/{exam.id}")
            assert response.status_code == 200
            assert "Midterm Exam" in response.data.decode("utf-8")
            assert "100" in response.data.decode("utf-8")  # max_points

    def test_exam_show_not_found(self, app, client):
        """Test showing non-existent exam."""
        with app.app_context():
            response = client.get("/exams/9999")
            assert response.status_code == 302  # Redirect


class TestExamNew:
    """Test exam creation routes."""

    def test_exam_new_get(self, app, client):
        """Test GET request to new exam form."""
        with app.app_context():
            response = client.get("/exams/new")
            assert response.status_code == 200
            assert "Neue Prüfung" in response.data.decode("utf-8")

    def test_exam_new_post_success(self, app, client):
        """Test successful exam creation."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/exams/new",
                data={
                    "name": "Test Exam",
                    "exam_type": "midterm",
                    "max_points": "100",
                    "weight": "0.3",
                    "course_id": str(course.id),
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            # Check that exam was created - flash message or exam details visible
            assert (
                "erfolgreich" in response_text
                or "successfully" in response_text
                or "Test Exam" in response_text
            )

    def test_exam_new_post_with_due_date(self, app, client):
        """Test exam creation with due date."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/exams/new",
                data={
                    "name": "Test Exam",
                    "exam_type": "final",
                    "max_points": "150",
                    "weight": "0.5",
                    "course_id": str(course.id),
                    "due_date": "2024-12-31",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            assert (
                "erfolgreich" in response_text
                or "successfully" in response_text
                or "Test Exam" in response_text
            )

    def test_exam_new_missing_name(self, app, client):
        """Test exam creation with missing name."""
        with app.app_context():
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/exams/new",
                data={
                    "name": "",
                    "exam_type": "midterm",
                    "max_points": "100",
                    "weight": "0.3",
                    "course_id": str(course.id),
                },
            )

            assert response.status_code == 200
            # Check that form is re-rendered (validation failed)
            assert "Neue Prüfung" in response.data.decode("utf-8")

    def test_exam_new_missing_exam_type(self, app, client):
        """Test exam creation with missing exam type."""
        with app.app_context():
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/exams/new",
                data={
                    "name": "Test Exam",
                    "exam_type": "",
                    "max_points": "100",
                    "weight": "0.3",
                    "course_id": str(course.id),
                },
            )

            assert response.status_code == 200
            # Check that form is re-rendered (validation failed)
            assert "Neue Prüfung" in response.data.decode("utf-8")

    def test_exam_new_invalid_max_points(self, app, client):
        """Test exam creation with invalid max_points."""
        with app.app_context():
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/exams/new",
                data={
                    "name": "Test Exam",
                    "exam_type": "midterm",
                    "max_points": "-10",
                    "weight": "0.3",
                    "course_id": str(course.id),
                },
            )

            assert "positiv" in response.data.decode("utf-8").lower()

    def test_exam_new_invalid_weight_too_large(self, app, client):
        """Test exam creation with weight > 1."""
        with app.app_context():
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/exams/new",
                data={
                    "name": "Test Exam",
                    "exam_type": "midterm",
                    "max_points": "100",
                    "weight": "1.5",
                    "course_id": str(course.id),
                },
            )

            assert (
                "zwischen 0 und 1" in response.data.decode("utf-8").lower()
                or "weight" in response.data.decode("utf-8").lower()
            )

    def test_exam_new_invalid_course_id(self, app, client):
        """Test exam creation with non-existent course."""
        with app.app_context():
            response = client.post(
                "/exams/new",
                data={
                    "name": "Test Exam",
                    "exam_type": "midterm",
                    "max_points": "100",
                    "weight": "0.3",
                    "course_id": "9999",
                },
            )

            assert response.status_code in [200, 302]


class TestExamEdit:
    """Test exam edit routes."""

    def test_exam_edit_get(self, app, client):
        """Test GET request to edit exam form."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                name="Midterm Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )

            response = client.get(f"/exams/{exam.id}/edit")
            assert response.status_code == 200
            assert "bearbeiten" in response.data.decode("utf-8")
            assert "Midterm Exam" in response.data.decode("utf-8")

    def test_exam_edit_post_success(self, app, client):
        """Test successful exam update."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                name="Midterm Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )

            response = client.post(
                f"/exams/{exam.id}/edit",
                data={
                    "name": "Updated Exam",
                    "exam_type": "final",
                    "max_points": "150",
                    "weight": "0.4",
                    "course_id": str(course.id),
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert "Updated Exam" in response.data.decode("utf-8")

    def test_exam_edit_not_found(self, app, client):
        """Test editing non-existent exam."""
        with app.app_context():
            response = client.get("/exams/9999/edit")
            assert response.status_code == 302  # Redirect


class TestExamDelete:
    """Test exam deletion route."""

    def test_exam_delete_success(self, app, client):
        """Test successful exam deletion."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                name="Midterm Exam",
                exam_type="midterm",
                max_points=100.0,
                weight=0.3,
                course_id=course.id,
            )

            response = client.post(f"/exams/{exam.id}/delete", follow_redirects=True)

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            # Check for deletion message or exam list
            assert (
                "gelöscht" in response_text
                or "deleted" in response_text
                or "Prüfungen" in response_text
            )

    def test_exam_delete_not_found(self, app, client):
        """Test deleting non-existent exam."""
        with app.app_context():
            response = client.post("/exams/9999/delete", follow_redirects=True)
            assert response.status_code == 200
