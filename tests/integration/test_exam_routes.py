"""
Integration tests for exam routes.

This module tests the Flask web interface for exam and exam component management.
"""

from datetime import date, timedelta

from cli.course_cli import add_course
from cli.exam_cli import add_exam, add_exam_component
from cli.university_cli import add_university


class TestExamListRoute:
    """Test exam list route."""

    def test_exam_list_empty(self, app, client):
        """Test exam list with no exams."""
        with app.app_context():
            response = client.get("/exams/")
            assert response.status_code == 200
            assert "Keine Prüfungen gefunden" in response.data.decode("utf-8")

    def test_exam_list_with_exams(self, app, client):
        """Test exam list with exams."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Statistics",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_exam(
                course_id=course.id,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )

            response = client.get("/exams/")
            assert response.status_code == 200
            assert "Final Exam" in response.data.decode("utf-8")
            assert "Introduction to Statistics" in response.data.decode("utf-8")


class TestExamCreateRoute:
    """Test exam create route."""

    def test_exam_create_get(self, app, client):
        """Test exam create form display."""
        with app.app_context():
            # Create a course for the dropdown
            university = add_university("TH Köln")
            add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.get("/exams/new")
            assert response.status_code == 200
            assert "Neue Prüfung" in response.data.decode("utf-8")
            assert "Test Course" in response.data.decode("utf-8")

    def test_exam_create_post_success(self, app, client):
        """Test successful exam creation."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )

            # Create exam
            future_date = (date.today() + timedelta(days=30)).isoformat()
            response = client.post(
                "/exams/new",
                data={
                    "course_id": str(course.id),
                    "name": "Midterm Exam",
                    "max_points": "80",
                    "weight": "0.4",
                    "due_date": future_date,
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            # Verify exam was created by checking the page shows the exam
            assert "Midterm Exam" in response.data.decode("utf-8")

    def test_exam_create_post_invalid_weight(self, app, client):
        """Test exam creation with invalid weight."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )

            # Try to create exam with invalid weight
            response = client.post(
                "/exams/new",
                data={
                    "course_id": str(course.id),
                    "name": "Invalid Exam",
                    "max_points": "100",
                    "weight": "1.5",  # Invalid: > 1.0
                },
            )

            # Should redirect due to error
            assert response.status_code == 302


class TestExamShowRoute:
    """Test exam detail route."""

    def test_exam_show_success(self, app, client):
        """Test displaying exam details."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                course_id=course.id,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )

            response = client.get(f"/exams/{exam.id}")
            assert response.status_code == 200
            assert "Final Exam" in response.data.decode("utf-8")
            assert "Test Course" in response.data.decode("utf-8")
            assert "100" in response.data.decode("utf-8")

    def test_exam_show_not_found(self, app, client):
        """Test displaying non-existent exam."""
        with app.app_context():
            response = client.get("/exams/99999", follow_redirects=True)
            assert response.status_code == 200
            # Should redirect to exam list page
            assert "Prüfungen" in response.data.decode("utf-8")


class TestExamEditRoute:
    """Test exam edit route."""

    def test_exam_edit_get(self, app, client):
        """Test exam edit form display."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                course_id=course.id,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )

            response = client.get(f"/exams/{exam.id}/edit")
            assert response.status_code == 200
            assert "Prüfung bearbeiten" in response.data.decode("utf-8")
            assert "Final Exam" in response.data.decode("utf-8")

    def test_exam_edit_post_success(self, app, client):
        """Test successful exam update."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                course_id=course.id,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )

            # Update exam
            response = client.post(
                f"/exams/{exam.id}/edit",
                data={
                    "name": "Updated Final Exam",
                    "max_points": "120",
                    "weight": "0.7",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            # Verify exam was updated
            assert "Updated Final Exam" in response.data.decode("utf-8")


class TestExamDeleteRoute:
    """Test exam delete route."""

    def test_exam_delete_success(self, app, client):
        """Test successful exam deletion."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                course_id=course.id,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )

            # Delete exam
            response = client.post(
                f"/exams/{exam.id}/delete",
                follow_redirects=True,
            )

            assert response.status_code == 200
            # Should redirect to exam list
            assert "Prüfungen" in response.data.decode("utf-8")


class TestExamComponentRoutes:
    """Test exam component routes."""

    def test_component_create_get(self, app, client):
        """Test component create form display."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                course_id=course.id,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )

            response = client.get(f"/exams/{exam.id}/components/new")
            assert response.status_code == 200
            assert "Neuer Teil" in response.data.decode("utf-8")
            assert "Final Exam" in response.data.decode("utf-8")

    def test_component_create_post_success(self, app, client):
        """Test successful component creation."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                course_id=course.id,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )

            # Create component
            response = client.post(
                f"/exams/{exam.id}/components/new",
                data={
                    "name": "Multiple Choice",
                    "max_points": "40",
                    "weight": "0.4",
                    "order": "1",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            # Verify component was created
            assert "Multiple Choice" in response.data.decode("utf-8")

    def test_component_edit_post_success(self, app, client):
        """Test successful component update."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                course_id=course.id,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )
            component = add_exam_component(
                exam_id=exam.id,
                name="Multiple Choice",
                max_points=40.0,
                weight=0.4,
                order=1,
            )

            # Update component
            response = client.post(
                f"/exams/{exam.id}/components/{component.id}/edit",
                data={
                    "name": "Updated Multiple Choice",
                    "max_points": "50",
                    "weight": "0.5",
                    "order": "1",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            # Verify component was updated
            assert "Updated Multiple Choice" in response.data.decode("utf-8")

    def test_component_delete_success(self, app, client):
        """Test successful component deletion."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                course_id=course.id,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )
            component = add_exam_component(
                exam_id=exam.id,
                name="Multiple Choice",
                max_points=40.0,
                weight=0.4,
                order=1,
            )

            # Delete component
            response = client.post(
                f"/exams/{exam.id}/components/{component.id}/delete",
                follow_redirects=True,
            )

            assert response.status_code == 200
            # Should redirect back to exam detail page
            assert "Final Exam" in response.data.decode("utf-8")

    def test_component_weight_validation_display(self, app, client):
        """Test that component weight validation is displayed."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            course = add_course(
                name="Test Course",
                semester="2024_WiSe",
                university_id=university.id,
            )
            exam = add_exam(
                course_id=course.id,
                name="Final Exam",
                max_points=100.0,
                weight=0.6,
            )

            # Add components with weights that sum to 1.0
            add_exam_component(
                exam_id=exam.id, name="Part 1", max_points=40.0, weight=0.4, order=1
            )
            add_exam_component(
                exam_id=exam.id, name="Part 2", max_points=60.0, weight=0.6, order=2
            )

            response = client.get(f"/exams/{exam.id}")
            assert response.status_code == 200
            # Should show success message for correct weights
            assert "korrekt" in response.data.decode("utf-8")
