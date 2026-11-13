"""
Unit tests for database indexes.

Verifies that frequently-queried columns have index=True or Index defined.
"""

import importlib
import inspect


class TestDatabaseIndexes:
    """Test that frequently-queried columns have database indexes."""

    def test_submission_enrollment_id_index(self):
        """Submission.enrollment_id should have an index."""
        source = inspect.getsource(
            importlib.import_module("app.models.submission").Submission
        )
        assert "enrollment_id" in source
        # Check column has index=True or __table_args__ has Index for it
        assert "index=True" in source or "idx_submission_enrollment" in source

    def test_grade_exam_id_index(self):
        """Grade.exam_id should have an index."""
        source = inspect.getsource(importlib.import_module("app.models.grade").Grade)
        assert "exam_id" in source
        assert "index=True" in source or "idx_grade_exam" in source

    def test_grade_enrollment_id_index(self):
        """Grade.enrollment_id should have an index."""
        source = inspect.getsource(importlib.import_module("app.models.grade").Grade)
        assert "enrollment_id" in source
        assert "index=True" in source or "idx_grade_enrollment" in source

    def test_page_annotation_document_id_index(self):
        """PageAnnotation.document_id should have an index."""
        source = inspect.getsource(
            importlib.import_module("app.models.page_annotation").PageAnnotation
        )
        assert "document_id" in source
        assert "index=True" in source

    def test_document_submission_id_index(self):
        """Document.submission_id should have an index."""
        source = inspect.getsource(
            importlib.import_module("app.models.document").Document
        )
        assert "submission_id" in source
        assert "index=True" in source or "idx_document_submission" in source

    def test_user_university_id_index(self):
        """User.university_id should have an index for user scoping."""
        source = inspect.getsource(importlib.import_module("app.models.user").User)
        assert "university_id" in source
        assert "index=True" in source

    def test_enrollment_course_id_index(self):
        """Enrollment.course_id should have an index."""
        source = inspect.getsource(
            importlib.import_module("app.models.enrollment").Enrollment
        )
        assert "course_id" in source
        assert "index=True" in source
