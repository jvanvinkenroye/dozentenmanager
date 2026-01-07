"""
Integration tests for enrollment routes.

This module tests the Flask web interface for enrollment management.
"""

from cli.course_cli import add_course
from cli.enrollment_cli import add_enrollment
import pytest

from app.services.student_service import StudentService

@pytest.fixture
def student_service():
    """Return a StudentService instance."""
    return StudentService()
from cli.university_cli import add_university


class TestEnrollmentRoute:
    """Test enrollment route."""

    def test_enroll_success(self, app, client, student_service):
        """Test successful student enrollment in course."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            # Enroll student
            response = client.post(
                "/enrollments/enroll",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert "erfolgreich" in response.data.decode("utf-8")
            assert "eingeschrieben" in response.data.decode("utf-8")

    def test_enroll_duplicate_prevented(self, app, client, student_service):
        """Test that duplicate enrollments are prevented."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            # First enrollment
            add_enrollment(student_id_str="12345678", course_id=course.id)

            # Try to enroll again
            response = client.post(
                "/enrollments/enroll",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                },
            )

            # Should redirect due to error
            assert response.status_code == 302

    def test_enroll_missing_student_id(self, app, client, student_service):
        """Test enrollment with missing student ID."""
        with app.app_context():
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/enrollments/enroll",
                data={"course_id": str(course.id)},
            )

            # Should redirect due to error
            assert response.status_code == 302

    def test_enroll_missing_course_id(self, app, client, student_service):
        """Test enrollment with missing course ID."""
        with app.app_context():
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )

            response = client.post(
                "/enrollments/enroll",
                data={"student_id": str(student.id)},
            )

            assert response.status_code == 302

    def test_enroll_invalid_student_id(self, app, client, student_service):
        """Test enrollment with non-existent student."""
        with app.app_context():
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/enrollments/enroll",
                data={"student_id": "99999", "course_id": str(course.id)},
            )

            assert response.status_code == 302

    def test_enroll_invalid_course_id(self, app, client, student_service):
        """Test enrollment with non-existent course."""
        with app.app_context():
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )

            response = client.post(
                "/enrollments/enroll",
                data={"student_id": str(student.id), "course_id": "99999"},
            )

            assert response.status_code == 302

    def test_enroll_non_numeric_ids(self, app, client, student_service):
        """Test enrollment with non-numeric IDs."""
        with app.app_context():
            response = client.post(
                "/enrollments/enroll",
                data={"student_id": "abc", "course_id": "xyz"},
            )

            assert response.status_code == 302

    def test_enroll_redirect_to_course(self, app, client, student_service):
        """Test that enrollment redirects to course page by default."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/enrollments/enroll",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                },
            )

            # Should redirect to course detail page
            assert response.status_code == 302
            assert f"/courses/{course.id}" in response.location

    def test_enroll_redirect_to_student(self, app, client, student_service):
        """Test that enrollment can redirect to student page."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/enrollments/enroll",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                    "redirect_to": "student",
                },
            )

            # Should redirect to student detail page
            assert response.status_code == 302
            assert "/students/12345678" in response.location


class TestUnenrollmentRoute:
    """Test unenrollment route."""

    def test_unenroll_success(self, app, client, student_service):
        """Test successful student unenrollment from course."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_enrollment(student_id_str="12345678", course_id=course.id)

            # Unenroll student
            response = client.post(
                "/enrollments/unenroll",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert "erfolgreich" in response.data.decode("utf-8")
            assert "ausgetragen" in response.data.decode("utf-8")

    def test_unenroll_non_existent(self, app, client, student_service):
        """Test unenrolling a non-existent enrollment."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            # Try to unenroll without enrollment
            response = client.post(
                "/enrollments/unenroll",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                },
            )

            assert response.status_code == 302

    def test_unenroll_missing_student_id(self, app, client, student_service):
        """Test unenrollment with missing student ID."""
        with app.app_context():
            university = add_university("TH Köln")
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            response = client.post(
                "/enrollments/unenroll",
                data={"course_id": str(course.id)},
            )

            assert response.status_code == 302

    def test_unenroll_missing_course_id(self, app, client, student_service):
        """Test unenrollment with missing course ID."""
        with app.app_context():
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )

            response = client.post(
                "/enrollments/unenroll",
                data={"student_id": str(student.id)},
            )

            assert response.status_code == 302

    def test_unenroll_non_numeric_ids(self, app, client, student_service):
        """Test unenrollment with non-numeric IDs."""
        with app.app_context():
            response = client.post(
                "/enrollments/unenroll",
                data={"student_id": "abc", "course_id": "xyz"},
            )

            assert response.status_code == 302

    def test_unenroll_redirect_to_course(self, app, client, student_service):
        """Test that unenrollment redirects to course page by default."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_enrollment(student_id_str="12345678", course_id=course.id)

            response = client.post(
                "/enrollments/unenroll",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                },
            )

            # Should redirect to course detail page
            assert response.status_code == 302
            assert f"/courses/{course.id}" in response.location

    def test_unenroll_redirect_to_student(self, app, client, student_service):
        """Test that unenrollment can redirect to student page."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_enrollment(student_id_str="12345678", course_id=course.id)

            response = client.post(
                "/enrollments/unenroll",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                    "redirect_to": "student",
                },
            )

            # Should redirect to student detail page
            assert response.status_code == 302
            assert "/students/12345678" in response.location


class TestUpdateStatusRoute:
    """Test enrollment status update route."""

    def test_update_status_success(self, app, client, student_service):
        """Test successful enrollment status update."""
        with app.app_context():
            # Create test data
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_enrollment(student_id_str="12345678", course_id=course.id)

            # Update status
            response = client.post(
                "/enrollments/status",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                    "status": "completed",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert "Status" in response.data.decode("utf-8")
            assert "aktualisiert" in response.data.decode("utf-8")

    def test_update_status_to_dropped(self, app, client, student_service):
        """Test updating status to dropped sets unenrollment date."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_enrollment(student_id_str="12345678", course_id=course.id)

            # Update status to dropped
            response = client.post(
                "/enrollments/status",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                    "status": "dropped",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert "aktualisiert" in response.data.decode("utf-8")

    def test_update_status_invalid(self, app, client, student_service):
        """Test updating status with invalid status value."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_enrollment(student_id_str="12345678", course_id=course.id)

            # Try invalid status
            response = client.post(
                "/enrollments/status",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                    "status": "invalid_status",
                },
            )

            assert response.status_code == 302

    def test_update_status_non_existent_enrollment(self, app, client, student_service):
        """Test updating status for non-existent enrollment."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )

            # Try to update without enrollment
            response = client.post(
                "/enrollments/status",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                    "status": "completed",
                },
            )

            assert response.status_code == 302

    def test_update_status_missing_parameters(self, app, client, student_service):
        """Test updating status with missing required parameters."""
        with app.app_context():
            response = client.post(
                "/enrollments/status",
                data={"student_id": "1"},
            )

            assert response.status_code == 302

    def test_update_status_non_numeric_ids(self, app, client, student_service):
        """Test updating status with non-numeric IDs."""
        with app.app_context():
            response = client.post(
                "/enrollments/status",
                data={"student_id": "abc", "course_id": "xyz", "status": "active"},
            )

            assert response.status_code == 302

    def test_update_status_redirect_to_course(self, app, client, student_service):
        """Test that status update redirects to course page by default."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_enrollment(student_id_str="12345678", course_id=course.id)

            response = client.post(
                "/enrollments/status",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                    "status": "completed",
                },
            )

            # Should redirect to course detail page
            assert response.status_code == 302
            assert f"/courses/{course.id}" in response.location

    def test_update_status_redirect_to_student(self, app, client, student_service):
        """Test that status update can redirect to student page."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_enrollment(student_id_str="12345678", course_id=course.id)

            response = client.post(
                "/enrollments/status",
                data={
                    "student_id": str(student.id),
                    "course_id": str(course.id),
                    "status": "completed",
                    "redirect_to": "student",
                },
            )

            # Should redirect to student detail page
            assert response.status_code == 302
            assert "/students/12345678" in response.location

    def test_update_all_valid_statuses(self, app, client, student_service):
        """Test updating to all valid status values."""
        with app.app_context():
            university = add_university("TH Köln")
            student = student_service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max.mustermann@example.com",
                program="Computer Science",
            )
            course = add_course(
                name="Introduction to Programming",
                semester="2024_WiSe",
                university_id=university.id,
            )
            add_enrollment(student_id_str="12345678", course_id=course.id)

            valid_statuses = ["active", "completed", "dropped"]

            for status in valid_statuses:
                response = client.post(
                    "/enrollments/status",
                    data={
                        "student_id": str(student.id),
                        "course_id": str(course.id),
                        "status": status,
                    },
                    follow_redirects=True,
                )

                assert response.status_code == 200
                assert "aktualisiert" in response.data.decode("utf-8")
