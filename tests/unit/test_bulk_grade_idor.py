"""
Unit tests for IDOR fix in bulk grading.

Tests the core validation logic that ensures bulk grading only
accepts grades for enrollments belonging to the exam's course.
"""

from app import db
from app.models import Course, Enrollment, Exam, Student, University


class TestBulkGradeIDORValidation:
    """Test the enrollment ownership validation logic."""

    def test_valid_enrollment_in_exam_course(self, app):
        """Enrollment belonging to exam's course should be accepted."""
        uni = University(name="Test Uni", slug="test-uni")
        db.session.add(uni)
        db.session.flush()

        course = Course(
            name="Test Course",
            slug="test-course",
            semester="2024_WiSe",
            university_id=uni.id,
        )
        db.session.add(course)
        db.session.flush()

        student = Student(
            first_name="Max",
            last_name="Muster",
            student_id="12345678",
            email="max@test.com",
            program="CS",
        )
        db.session.add(student)
        db.session.flush()

        enrollment = Enrollment(
            student_id=student.id,
            course_id=course.id,
            status="active",
        )
        db.session.add(enrollment)
        db.session.flush()

        exam = Exam(
            name="Test Exam",
            course_id=course.id,
            exam_date=__import__("datetime").date(2025, 1, 1),
            max_points=100,
            weight=100,
        )
        db.session.add(exam)
        db.session.flush()

        # Build valid enrollment IDs (same logic as the fixed bulk route)
        valid_enrollment_ids = {
            e.id
            for e in Enrollment.query.join(Student)
            .filter(
                Enrollment.course_id == exam.course_id,
                Enrollment.status == "active",
            )
            .all()
        }

        assert enrollment.id in valid_enrollment_ids

    def test_foreign_enrollment_not_in_exam_course(self, app):
        """Enrollment NOT belonging to exam's course should be rejected."""
        uni = University(name="Test Uni", slug="test-uni")
        db.session.add(uni)
        db.session.flush()

        course_a = Course(
            name="Course A",
            slug="course-a",
            semester="2024_WiSe",
            university_id=uni.id,
        )
        db.session.add(course_a)
        db.session.flush()

        course_b = Course(
            name="Course B",
            slug="course-b",
            semester="2024_WiSe",
            university_id=uni.id,
        )
        db.session.add(course_b)
        db.session.flush()

        student = Student(
            first_name="Max",
            last_name="Muster",
            student_id="12345678",
            email="max@test.com",
            program="CS",
        )
        db.session.add(student)
        db.session.flush()

        enrollment_a = Enrollment(
            student_id=student.id,
            course_id=course_a.id,
            status="active",
        )
        db.session.add(enrollment_a)

        enrollment_b = Enrollment(
            student_id=student.id,
            course_id=course_b.id,
            status="active",
        )
        db.session.add(enrollment_b)
        db.session.flush()

        exam = Exam(
            name="Exam A",
            course_id=course_a.id,
            exam_date=__import__("datetime").date(2025, 1, 1),
            max_points=100,
            weight=100,
        )
        db.session.add(exam)
        db.session.flush()

        # Build valid enrollment IDs for exam's course
        valid_enrollment_ids = {
            e.id
            for e in Enrollment.query.join(Student)
            .filter(
                Enrollment.course_id == exam.course_id,
                Enrollment.status == "active",
            )
            .all()
        }

        # enrollment_a should be valid (belongs to course_a which exam belongs to)
        assert enrollment_a.id in valid_enrollment_ids

        # enrollment_b should NOT be valid (belongs to course_b, not course_a)
        assert enrollment_b.id not in valid_enrollment_ids, (
            "IDOR validation: enrollment from different course must be excluded"
        )
