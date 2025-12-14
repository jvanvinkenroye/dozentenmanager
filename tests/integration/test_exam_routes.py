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


class TestExamComponentAdd:
    """Test adding exam components."""

    def test_add_component_success(self, app, client):
        """Test successfully adding a component to an exam."""
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

            # Add component
            response = client.post(
                f"/exams/{exam.id}/components/add",
                data={
                    "name": "Written Part",
                    "description": "Written exam part",
                    "max_points": "60.0",
                    "weight": "0.6",
                    "order": "0",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            assert "Written Part" in response_text
            assert "60" in response_text

    def test_add_component_missing_name(self, app, client):
        """Test adding component without name."""
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

            # Try to add component without name
            response = client.post(
                f"/exams/{exam.id}/components/add",
                data={
                    "name": "",
                    "max_points": "60.0",
                    "weight": "0.6",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            assert "erforderlich" in response_text or "required" in response_text

    def test_add_component_weight_exceeds_limit(self, app, client):
        """Test adding component that would exceed total weight of 1.0."""
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

            # Add first component with weight 0.6
            client.post(
                f"/exams/{exam.id}/components/add",
                data={
                    "name": "Part 1",
                    "max_points": "60.0",
                    "weight": "0.6",
                },
            )

            # Try to add second component with weight 0.6 (would exceed 1.0)
            response = client.post(
                f"/exams/{exam.id}/components/add",
                data={
                    "name": "Part 2",
                    "max_points": "60.0",
                    "weight": "0.6",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            # Should show error about exceeding available weight
            assert (
                "available" in response_text.lower()
                or "verfügbar" in response_text.lower()
            )


class TestExamComponentUpdate:
    """Test updating exam components."""

    def test_update_component_success(self, app, client):
        """Test successfully updating a component."""
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

            # Add component
            from cli.exam_component_cli import add_component

            component = add_component(
                name="Written Part",
                max_points=60.0,
                weight=0.6,
                exam_id=exam.id,
            )

            # Update component name
            response = client.post(
                f"/exams/components/{component.id}/update",
                data={"name": "Updated Part"},
                follow_redirects=True,
            )

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            assert "Updated Part" in response_text

    def test_update_component_weight(self, app, client):
        """Test updating component weight."""
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

            # Add two components
            from cli.exam_component_cli import add_component

            component1 = add_component(
                name="Part 1", max_points=60.0, weight=0.6, exam_id=exam.id
            )
            add_component(name="Part 2", max_points=40.0, weight=0.4, exam_id=exam.id)

            # Update first component weight to 0.5
            response = client.post(
                f"/exams/components/{component1.id}/update",
                data={"weight": "0.5"},
                follow_redirects=True,
            )

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            assert "50%" in response_text or "0.5" in response_text

    def test_update_component_not_found(self, app, client):
        """Test updating non-existent component."""
        with app.app_context():
            response = client.post(
                "/exams/components/9999/update",
                data={"name": "Updated"},
                follow_redirects=True,
            )

            assert response.status_code == 200


class TestExamComponentDelete:
    """Test deleting exam components."""

    def test_delete_component_success(self, app, client):
        """Test successfully deleting a component."""
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

            # Add component
            from cli.exam_component_cli import add_component

            component = add_component(
                name="Written Part",
                max_points=60.0,
                weight=0.6,
                exam_id=exam.id,
            )

            # Delete component
            response = client.post(
                f"/exams/components/{component.id}/delete", follow_redirects=True
            )

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            assert "gelöscht" in response_text or "deleted" in response_text.lower()

    def test_delete_component_not_found(self, app, client):
        """Test deleting non-existent component."""
        with app.app_context():
            response = client.post(
                "/exams/components/9999/delete", follow_redirects=True
            )

            assert response.status_code == 200


class TestExamComponentDisplay:
    """Test exam component display in exam detail view."""

    def test_exam_detail_shows_components(self, app, client):
        """Test that exam detail page displays components."""
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

            # Add components
            from cli.exam_component_cli import add_component

            add_component(
                name="Written Part",
                description="Written exam",
                max_points=60.0,
                weight=0.6,
                exam_id=exam.id,
                order=0,
            )
            add_component(
                name="Practical Part",
                description="Practical exam",
                max_points=40.0,
                weight=0.4,
                exam_id=exam.id,
                order=1,
            )

            # View exam detail page
            response = client.get(f"/exams/{exam.id}")

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            assert "Written Part" in response_text
            assert "Practical Part" in response_text
            assert "Written exam" in response_text
            assert "Practical exam" in response_text

    def test_exam_detail_shows_weight_validation(self, app, client):
        """Test that exam detail page shows weight validation status."""
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

            # Add components totaling 1.0
            from cli.exam_component_cli import add_component

            add_component(name="Part 1", max_points=60.0, weight=0.6, exam_id=exam.id)
            add_component(name="Part 2", max_points=40.0, weight=0.4, exam_id=exam.id)

            # View exam detail page
            response = client.get(f"/exams/{exam.id}")

            assert response.status_code == 200
            response_text = response.data.decode("utf-8")
            # Should show valid weight (100%)
            assert "100%" in response_text
            # Should show success indicator
            assert "✓" in response_text or "success" in response_text
