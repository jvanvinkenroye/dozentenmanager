"""
Document service for business logic layer.

This module provides business logic for document and submission management,
handling uploads, listing, deletion, and status updates.
"""

import logging
import mimetypes
import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from flask import current_app
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.course import Course
from app.models.document import (
    ALLOWED_EXTENSIONS,
    Document,
    allowed_file,
    get_file_extension,
    sanitize_filename,
)
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.student import Student
from app.models.submission import (
    VALID_SUBMISSION_STATUSES,
    VALID_SUBMISSION_TYPES,
    Submission,
)
from app.services.base_service import BaseService

# Configure logging
logger = logging.getLogger(__name__)


class DocumentService(BaseService):
    """
    Service class for document and submission management.

    Provides methods for uploading, listing, retrieving, and deleting documents,
    as well as managing submissions and their statuses.
    """

    def get_upload_path(
        self,
        enrollment: Enrollment,
        filename: str,
        base_path: str | None = None,
    ) -> str:
        """
        Generate organized upload path for a document.

        Path structure: uploads/{university_slug}/{semester}/{course_slug}/{StudentName}/

        Args:
            enrollment: Enrollment object containing course and student info
            filename: Sanitized filename
            base_path: Base upload directory (optional, defaults to app config)

        Returns:
            Full file path for storage
        """
        course = enrollment.course
        student = enrollment.student
        university = course.university

        # Create path components
        if base_path is None:
            base_path = current_app.config.get("UPLOAD_FOLDER", "uploads")
        university_slug = university.slug
        semester = course.semester
        course_slug = course.slug
        student_folder = f"{student.last_name}{student.first_name}"

        # Build path
        path = (
            Path(base_path) / university_slug / semester / course_slug / student_folder
        )
        path.mkdir(parents=True, exist_ok=True)

        # Generate unique filename if file already exists
        final_path = path / filename
        counter = 1
        while final_path.exists():
            name, ext = os.path.splitext(filename)
            final_path = path / f"{name}_{counter}{ext}"
            counter += 1

        return str(final_path)

    def create_submission(
        self,
        enrollment_id: int,
        submission_type: str = "document",
        exam_id: int | None = None,
        notes: str | None = None,
    ) -> Submission:
        """
        Create a new submission record.

        Args:
            enrollment_id: Enrollment ID for this submission
            submission_type: Type of submission (document, assignment, etc.)
            exam_id: Optional exam ID if submission is for an exam
            notes: Optional notes about the submission

        Returns:
            Created Submission object

        Raises:
            ValueError: If validation fails
            IntegrityError: If database constraint fails
        """
        # Validate enrollment exists
        enrollment = self.query(Enrollment).filter_by(id=enrollment_id).first()
        if not enrollment:
            raise ValueError(f"Enrollment with ID {enrollment_id} not found")

        # Validate submission type
        if submission_type not in VALID_SUBMISSION_TYPES:
            raise ValueError(
                f"Invalid submission type. Must be one of: {', '.join(VALID_SUBMISSION_TYPES)}"
            )

        # Validate exam if provided
        if exam_id:
            exam = self.query(Exam).filter_by(id=exam_id).first()
            if not exam:
                raise ValueError(f"Exam with ID {exam_id} not found")

        try:
            submission = Submission(
                enrollment_id=enrollment_id,
                submission_type=submission_type,
                exam_id=exam_id,
                notes=notes,
                submission_date=datetime.now(UTC),
                status="submitted",
            )
            self.add(submission)
            self.commit()

            logger.info(
                f"Created submission ID {submission.id} for enrollment {enrollment_id}"
            )
            return submission

        except IntegrityError as e:
            self.rollback()
            logger.error(f"Database constraint error while creating submission: {e}")
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while creating submission: {e}")
            raise ValueError(f"Failed to create submission: {e}") from e

    def upload_document(
        self,
        file_path: str,
        enrollment_id: int,
        submission_type: str = "document",
        exam_id: int | None = None,
        notes: str | None = None,
    ) -> Document:
        """
        Upload a document for a student enrollment.

        Args:
            file_path: Path to the file to upload
            enrollment_id: Enrollment ID for this document
            submission_type: Type of submission
            exam_id: Optional exam ID if document is for an exam
            notes: Optional notes about the submission

        Returns:
            Created Document object

        Raises:
            ValueError: If validation fails
            FileNotFoundError: If source file doesn't exist
            IntegrityError: If database constraint fails
        """
        # Validate file exists
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Validate file extension
        original_filename = source_path.name
        if not allowed_file(original_filename):
            raise ValueError(
                f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Validate enrollment
        enrollment = self.query(Enrollment).filter_by(id=enrollment_id).first()
        if not enrollment:
            raise ValueError(f"Enrollment with ID {enrollment_id} not found")

        # Sanitize filename
        safe_filename = sanitize_filename(original_filename)

        # Get file info
        file_size = source_path.stat().st_size
        file_type = get_file_extension(original_filename)
        mime_type, _ = mimetypes.guess_type(original_filename)

        try:
            # Create submission first
            submission = self.create_submission(
                enrollment_id=enrollment_id,
                submission_type=submission_type,
                exam_id=exam_id,
                notes=notes,
            )

            # Generate destination path
            dest_path = self.get_upload_path(enrollment, safe_filename)

            # Copy file to destination
            shutil.copy2(str(source_path), dest_path)

            # Create document record
            document = Document(
                submission_id=submission.id,
                filename=safe_filename,
                original_filename=original_filename,
                file_path=dest_path,
                file_type=file_type,
                file_size=file_size,
                mime_type=mime_type,
                upload_date=datetime.now(UTC),
            )
            self.add(document)
            self.commit()

            logger.info(
                f"Uploaded document: {original_filename} -> {dest_path} "
                f"(submission ID: {submission.id})"
            )
            return document

        except (ValueError, IntegrityError):
            # Re-raise validation and constraint errors
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while uploading document: {e}")
            raise ValueError(f"Failed to upload document: {e}") from e

    def list_documents(
        self,
        enrollment_id: int | None = None,
        submission_id: int | None = None,
        file_type: str | None = None,
        course_id: int | None = None,
        student_id: int | None = None,
        status: str | None = None,
    ) -> list[Document]:
        """
        List documents with optional filters.

        Args:
            enrollment_id: Optional enrollment ID filter
            submission_id: Optional submission ID filter
            file_type: Optional file type filter
            course_id: Optional course ID filter
            student_id: Optional student ID filter
            status: Optional submission status filter

        Returns:
            List of Document objects matching the filters
        """
        try:
            query = (
                self.query(Document)
                .join(Submission)
                .join(Enrollment)
                .join(Student)
                .join(Course)
            )

            if enrollment_id:
                query = query.filter(Submission.enrollment_id == enrollment_id)

            if submission_id:
                query = query.filter(Document.submission_id == submission_id)

            if file_type:
                query = query.filter(Document.file_type == file_type.lower())

            if course_id:
                query = query.filter(Course.id == course_id)

            if student_id:
                query = query.filter(Student.id == student_id)

            if status:
                query = query.filter(Submission.status == status)

            return query.order_by(Document.upload_date.desc()).all()

        except SQLAlchemyError as e:
            logger.error(f"Database error while listing documents: {e}")
            return []

    def get_document(self, document_id: int) -> Document:
        """
        Get a document by ID.

        Args:
            document_id: Document database ID

        Returns:
            Document object

        Raises:
            ValueError: If document not found
        """
        try:
            document = self.query(Document).filter_by(id=document_id).first()
            if not document:
                raise ValueError(f"Document with ID {document_id} not found")
            return document

        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching document: {e}")
            raise ValueError(f"Failed to fetch document: {e}") from e

    def delete_document(self, document_id: int, delete_file: bool = True) -> bool:
        """
        Delete a document from the database and optionally from disk.

        Args:
            document_id: Document database ID
            delete_file: Whether to delete the physical file (default: True)

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If document not found
        """
        try:
            document = self.query(Document).filter_by(id=document_id).first()

            if not document:
                raise ValueError(f"Document with ID {document_id} not found")

            file_path = document.file_path
            document_name = document.original_filename

            # Delete database record
            self.delete(document)
            self.commit()

            # Delete physical file if requested
            if delete_file and file_path:
                try:
                    Path(file_path).unlink(missing_ok=True)
                    logger.info(f"Deleted file: {file_path}")
                except OSError as e:
                    logger.warning(f"Could not delete file {file_path}: {e}")

            logger.info(f"Deleted document: {document_name}")
            return True

        except ValueError:
            # Re-raise validation errors
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while deleting document: {e}")
            raise ValueError(f"Failed to delete document: {e}") from e

    def list_submissions(
        self,
        enrollment_id: int | None = None,
        exam_id: int | None = None,
        status: str | None = None,
        course_id: int | None = None,
    ) -> list[Submission]:
        """
        List submissions with optional filters.

        Args:
            enrollment_id: Optional enrollment ID filter
            exam_id: Optional exam ID filter
            status: Optional status filter
            course_id: Optional course ID filter

        Returns:
            List of Submission objects matching the filters
        """
        try:
            query = self.query(Submission).join(Enrollment).join(Course)

            if enrollment_id:
                query = query.filter(Submission.enrollment_id == enrollment_id)

            if exam_id:
                query = query.filter(Submission.exam_id == exam_id)

            if status:
                query = query.filter(Submission.status == status)

            if course_id:
                query = query.filter(Course.id == course_id)

            return query.order_by(Submission.submission_date.desc()).all()

        except SQLAlchemyError as e:
            logger.error(f"Database error while listing submissions: {e}")
            return []

    def get_submission(self, submission_id: int) -> Submission:
        """
        Get a submission by ID.

        Args:
            submission_id: Submission database ID

        Returns:
            Submission object

        Raises:
            ValueError: If submission not found
        """
        try:
            submission = self.query(Submission).filter_by(id=submission_id).first()
            if not submission:
                raise ValueError(f"Submission with ID {submission_id} not found")
            return submission

        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching submission: {e}")
            raise ValueError(f"Failed to fetch submission: {e}") from e

    def update_submission_status(
        self,
        submission_id: int,
        status: str,
        notes: str | None = None,
    ) -> Submission:
        """
        Update the status of a submission.

        Args:
            submission_id: Submission database ID
            status: New status value
            notes: Optional notes to update

        Returns:
            Updated Submission object

        Raises:
            ValueError: If validation fails
        """
        if status not in VALID_SUBMISSION_STATUSES:
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(VALID_SUBMISSION_STATUSES)}"
            )

        try:
            submission = self.query(Submission).filter_by(id=submission_id).first()

            if not submission:
                raise ValueError(f"Submission with ID {submission_id} not found")

            submission.status = status
            if notes is not None:
                submission.notes = notes

            self.commit()

            logger.info(f"Updated submission {submission_id} status to: {status}")
            return submission

        except ValueError:
            # Re-raise validation errors
            raise

        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Database error while updating submission status: {e}")
            raise ValueError(f"Failed to update submission status: {e}") from e

    def match_file_to_enrollment(
        self,
        filename: str,
        course_id: int,
    ) -> Enrollment | None:
        """
        Try to match a filename to a student enrollment.

        Attempts to extract student name from filename and match to enrollment.

        Args:
            filename: Original filename
            course_id: Course ID to search enrollments

        Returns:
            Matching Enrollment or None if no match found
        """
        try:
            # Remove extension
            name_part = os.path.splitext(filename)[0]

            # Normalize separators
            name_part = re.sub(r"[-_\s]+", "", name_part)

            # Get all enrollments for the course
            enrollments = (
                self.query(Enrollment)
                .join(Student)
                .filter(Enrollment.course_id == course_id)
                .filter(Enrollment.status == "active")
                .all()
            )

            for enrollment in enrollments:
                student = enrollment.student
                # Create normalized student name patterns
                pattern1 = f"{student.last_name}{student.first_name}".lower()
                pattern2 = f"{student.first_name}{student.last_name}".lower()

                name_lower = name_part.lower()

                if name_lower.startswith(pattern1) or name_lower.startswith(pattern2):
                    return enrollment

            return None

        except SQLAlchemyError as e:
            logger.error(f"Database error while matching file to enrollment: {e}")
            return None
