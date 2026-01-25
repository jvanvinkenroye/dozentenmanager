"""
Integration tests for enrollment routes.

This module tests the Flask web interface for enrollment management.
"""

import pytest

from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService
from app.services.student_service import StudentService
from app.services.university_service import UniversityService


@pytest.fixture
def student_service():
    """Return a StudentService instance."""
    return StudentService()


@pytest.fixture
def course_service():
    """Return a CourseService instance."""
    return CourseService()


@pytest.fixture
def university_service():
    """Return a UniversityService instance."""
    return UniversityService()


@pytest.fixture
def enrollment_service():
    """Return an EnrollmentService instance."""
    return EnrollmentService()


class TestEnrollmentRoute:
    """Test enrollment route."""

    def test_enroll_success(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test successful student enrollment in course."""
        # Create test data
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )

        # Enroll student
        response = auth_client.post(
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

    def test_enroll_duplicate_prevented(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test that duplicate enrollments are prevented."""
        # Create test data
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )

        # First enrollment
        enrollment_service.add_enrollment(
            student_id_str="12345678", course_id=course.id
        )

        # Try to enroll again
        response = auth_client.post(
            "/enrollments/enroll",
            data={
                "student_id": str(student.id),
                "course_id": str(course.id),
            },
        )

        # Should redirect due to error
        assert response.status_code == 302

    def test_enroll_missing_student_id(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test enrollment with missing student ID."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )

        response = auth_client.post(
            "/enrollments/enroll",
            data={"course_id": str(course.id)},
        )

        # Should redirect due to error
        assert response.status_code == 302

    def test_enroll_missing_course_id(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test enrollment with missing course ID."""
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )

        response = auth_client.post(
            "/enrollments/enroll",
            data={"student_id": str(student.id)},
        )

        assert response.status_code == 302

    def test_enroll_invalid_student_id(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test enrollment with non-existent student."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )

        response = auth_client.post(
            "/enrollments/enroll",
            data={"student_id": "99999", "course_id": str(course.id)},
        )

        assert response.status_code == 302

    def test_enroll_invalid_course_id(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test enrollment with non-existent course."""
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )

        response = auth_client.post(
            "/enrollments/enroll",
            data={"student_id": str(student.id), "course_id": "99999"},
        )

        assert response.status_code == 302

    def test_enroll_non_numeric_ids(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test enrollment with non-numeric IDs."""
        response = auth_client.post(
            "/enrollments/enroll",
            data={"student_id": "abc", "course_id": "xyz"},
        )

        assert response.status_code == 302

    def test_enroll_redirect_to_course(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test that enrollment redirects to course page by default."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )

        response = auth_client.post(
            "/enrollments/enroll",
            data={
                "student_id": str(student.id),
                "course_id": str(course.id),
            },
        )

        # Should redirect to course detail page
        assert response.status_code == 302
        assert f"/courses/{course.id}" in response.location

    def test_enroll_redirect_to_student(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test that enrollment can redirect to student page."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )

        response = auth_client.post(
            "/enrollments/enroll",
            data={
                "student_id": str(student.id),
                "course_id": str(course.id),
                "redirect_to": "student",
            },
        )

        # Should redirect to student detail page
        assert response.status_code == 302
        assert f"/students/{student.id}" in response.location


class TestUnenrollmentRoute:
    """Test unenrollment route."""

    def test_unenroll_success(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test successful student unenrollment from course."""
        # Create test data
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        enrollment_service.add_enrollment(
            student_id_str="12345678", course_id=course.id
        )

        # Unenroll student
        response = auth_client.post(
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

    def test_unenroll_non_existent(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test unenrolling a non-existent enrollment."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )

        # Try to unenroll without enrollment
        response = auth_client.post(
            "/enrollments/unenroll",
            data={
                "student_id": str(student.id),
                "course_id": str(course.id),
            },
        )

        assert response.status_code == 302

    def test_unenroll_missing_student_id(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test unenrollment with missing student ID."""
        university = university_service.add_university("TH Köln")
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )

        response = auth_client.post(
            "/enrollments/unenroll",
            data={"course_id": str(course.id)},
        )

        assert response.status_code == 302

    def test_unenroll_missing_course_id(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test unenrollment with missing course ID."""
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )

        response = auth_client.post(
            "/enrollments/unenroll",
            data={"student_id": str(student.id)},
        )

        assert response.status_code == 302

    def test_unenroll_non_numeric_ids(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test unenrollment with non-numeric IDs."""
        response = auth_client.post(
            "/enrollments/unenroll",
            data={"student_id": "abc", "course_id": "xyz"},
        )

        assert response.status_code == 302

    def test_unenroll_redirect_to_course(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test that unenrollment redirects to course page by default."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        enrollment_service.add_enrollment(
            student_id_str="12345678", course_id=course.id
        )

        response = auth_client.post(
            "/enrollments/unenroll",
            data={
                "student_id": str(student.id),
                "course_id": str(course.id),
            },
        )

        # Should redirect to course detail page
        assert response.status_code == 302
        assert f"/courses/{course.id}" in response.location

    def test_unenroll_redirect_to_student(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test that unenrollment can redirect to student page."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        enrollment_service.add_enrollment(
            student_id_str="12345678", course_id=course.id
        )

        response = auth_client.post(
            "/enrollments/unenroll",
            data={
                "student_id": str(student.id),
                "course_id": str(course.id),
                "redirect_to": "student",
            },
        )

        # Should redirect to student detail page
        assert response.status_code == 302
        assert f"/students/{student.id}" in response.location


class TestUpdateStatusRoute:
    """Test enrollment status update route."""

    def test_update_status_success(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test successful enrollment status update."""
        # Create test data
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        enrollment_service.add_enrollment(
            student_id_str="12345678", course_id=course.id
        )

        # Update status
        response = auth_client.post(
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

    def test_update_status_to_dropped(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test updating status to dropped sets unenrollment date."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        enrollment_service.add_enrollment(
            student_id_str="12345678", course_id=course.id
        )

        # Update status to dropped
        response = auth_client.post(
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

    def test_update_status_invalid(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test updating status with invalid status value."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        enrollment_service.add_enrollment(
            student_id_str="12345678", course_id=course.id
        )

        # Try invalid status
        response = auth_client.post(
            "/enrollments/status",
            data={
                "student_id": str(student.id),
                "course_id": str(course.id),
                "status": "invalid_status",
            },
        )

        assert response.status_code == 302

    def test_update_status_non_existent_enrollment(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test updating status for non-existent enrollment."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )

        # Try to update without enrollment
        response = auth_client.post(
            "/enrollments/status",
            data={
                "student_id": str(student.id),
                "course_id": str(course.id),
                "status": "completed",
            },
        )

        assert response.status_code == 302

    def test_update_status_missing_parameters(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test updating status with missing required parameters."""
        response = auth_client.post(
            "/enrollments/status",
            data={"student_id": "1"},
        )

        assert response.status_code == 302

    def test_update_status_non_numeric_ids(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test updating status with non-numeric IDs."""
        response = auth_client.post(
            "/enrollments/status",
            data={"student_id": "abc", "course_id": "xyz", "status": "active"},
        )

        assert response.status_code == 302

    def test_update_status_redirect_to_course(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test that status update redirects to course page by default."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        enrollment_service.add_enrollment(
            student_id_str="12345678", course_id=course.id
        )

        response = auth_client.post(
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

    def test_update_status_redirect_to_student(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test that status update can redirect to student page."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        enrollment_service.add_enrollment(
            student_id_str="12345678", course_id=course.id
        )

        response = auth_client.post(
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
        assert f"/students/{student.id}" in response.location

    def test_update_all_valid_statuses(
        self,
        app,
        auth_client,
        student_service,
        university_service,
        course_service,
        enrollment_service,
    ):
        """Test updating to all valid status values."""
        university = university_service.add_university("TH Köln")
        student = student_service.add_student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max.mustermann@example.com",
            program="Computer Science",
        )
        course = course_service.add_course(
            name="Introduction to Programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        enrollment_service.add_enrollment(
            student_id_str="12345678", course_id=course.id
        )

        valid_statuses = ["active", "completed", "dropped"]

        for status in valid_statuses:
            response = auth_client.post(
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
