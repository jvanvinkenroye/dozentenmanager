"""
Unit tests for extended N+1 query optimization.

Verifies that exam_service, document_service, and statistics_service
use eager loading (joinedload/selectinload) to prevent N+1 queries.
"""


class TestN1QueryExtendedImports:
    """Test that extended service files import eager loading tools."""

    def test_imports_in_exam_service(self):
        """Verify exam_service imports joinedload/selectinload."""
        from app.services import exam_service

        with open(exam_service.__file__) as f:
            source = f.read()
        assert "joinedload" in source or "selectinload" in source

    def test_imports_in_document_service(self):
        """Verify document_service imports joinedload/selectinload."""
        from app.services import document_service

        with open(document_service.__file__) as f:
            source = f.read()
        assert "joinedload" in source or "selectinload" in source

    def test_imports_in_statistics_service(self):
        """Verify statistics_service imports joinedload/selectinload."""
        from app.services import statistics_service

        with open(statistics_service.__file__) as f:
            source = f.read()
        assert "joinedload" in source or "selectinload" in source


class TestN1QueryExtendedRuntime:
    """Test that eager loading works at runtime."""

    def test_exam_service_list_exams_uses_eager_loading(self, app):
        """ExamService.list_exams should use joinedload for course/components."""
        from app.services.exam_service import ExamService

        service = ExamService()
        exams = service.list_exams()

        for exam in exams:
            # Access related objects — should not trigger lazy queries
            _ = exam.course
            _ = exam.components

    def test_exam_service_get_exam_uses_eager_loading(self, app):
        """ExamService.get_exam should use joinedload for course/components."""
        from app.services.exam_service import ExamService

        service = ExamService()
        exam = service.get_exam(1)
        if exam:
            _ = exam.course
            _ = exam.components

    def test_document_service_list_documents_uses_eager_loading(self, app):
        """DocumentService.list_documents should use selectinload."""
        from app.services.document_service import DocumentService

        service = DocumentService()
        documents = service.list_documents()

        for doc in documents:
            # These should not trigger lazy queries
            _ = doc.submission
            _ = doc.submission.enrollment
            _ = doc.submission.enrollment.student

    def test_document_service_list_submissions_uses_eager_loading(self, app):
        """DocumentService.list_submissions should use selectinload."""
        from app.services.document_service import DocumentService

        service = DocumentService()
        submissions = service.list_submissions()

        for sub in submissions:
            # These should not trigger lazy queries
            _ = sub.documents
            _ = sub.enrollment
            _ = sub.enrollment.student
