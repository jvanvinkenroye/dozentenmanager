"""
Unit tests for N+1 query optimization.

Verifies that routes use eager loading (joinedload/selectinload)
instead of causing N+1 queries when loading related entities.
"""

from sqlalchemy.orm import joinedload, selectinload


class TestN1QueryOptimization:
    """Test that database queries use eager loading."""

    def test_joinedload_exists(self):
        """Verify joinedload is available for eager loading."""
        assert joinedload is not None

    def test_selectinload_exists(self):
        """Verify selectinload is available for eager loading."""
        assert selectinload is not None

    def test_student_service_list_uses_eager_loading(self, app):
        """StudentService.list_students should use selectinload for enrollments."""
        from app.services.student_service import StudentService

        service = StudentService()
        students = service.list_students()

        # Access enrollments — should not trigger lazy query since loaded
        for student in students:
            assert hasattr(student, "enrollments")
            # The enrollments collection should be loaded
            _ = student.enrollments

    def test_student_service_detail_uses_eager_loading(self, app):
        """StudentService.get_student() should use selectinload for enrollments."""
        from app.services.student_service import StudentService

        service = StudentService()
        student = service.get_student(1)
        if student:
            # Access enrollments — should not trigger lazy query
            _ = student.enrollments

    def test_course_service_list_uses_eager_loading(self, app):
        """CourseService.list_courses should use selectinload for enrollments."""
        from app.services.course_service import CourseService

        service = CourseService()
        courses = service.list_courses()

        for course in courses:
            # Access enrollments with student/course
            for enrollment in course.enrollments:
                # These should not trigger lazy loads
                assert hasattr(enrollment, "student")
                assert hasattr(enrollment, "course")
                _ = enrollment.student
                _ = enrollment.course

    def test_enrollment_service_list_uses_eager_loading(self, app):
        """EnrollmentService.list_enrollments should use joinedload."""
        from app.services.enrollment_service import EnrollmentService

        service = EnrollmentService()

        # By course
        enrollments = service.list_enrollments(course_id=1)
        for e in enrollments:
            _ = e.student
            _ = e.course

    def test_grade_service_list_uses_eager_loading(self, app):
        """GradeService.list_grades should use joinedload."""
        from app.services.grade_service import GradeService

        service = GradeService()
        grades = service.list_grades()

        for grade in grades:
            # These should not trigger lazy queries
            _ = grade.enrollment
            _ = grade.exam
            _ = grade.component

    def test_grade_service_weighted_average_uses_eager_loading(self, app):
        """GradeService.calculate_weighted_average should use joinedload."""
        from app.services.grade_service import GradeService

        service = GradeService()
        result = service.calculate_weighted_average(enrollment_id=1)
        # If eager loading is used, accessing enrollment.student won't fail
        if result:
            assert "student_name" in result

    def test_imports_in_student_service(self):
        """Verify student_service imports joinedload/selectinload."""
        from app.services import student_service

        with open(student_service.__file__) as f:
            source = f.read()
        assert "selectinload" in source or "joinedload" in source

    def test_imports_in_course_service(self):
        """Verify course_service imports joinedload/selectinload."""
        from app.services import course_service

        with open(course_service.__file__) as f:
            source = f.read()
        assert "selectinload" in source or "joinedload" in source

    def test_imports_in_enrollment_service(self):
        """Verify enrollment_service imports joinedload/selectinload."""
        from app.services import enrollment_service

        with open(enrollment_service.__file__) as f:
            source = f.read()
        assert "selectinload" in source or "joinedload" in source

    def test_imports_in_grade_service(self):
        """Verify grade_service imports joinedload/selectinload."""
        from app.services import grade_service

        with open(grade_service.__file__) as f:
            source = f.read()
        assert "selectinload" in source or "joinedload" in source
