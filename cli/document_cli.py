"""
Document management CLI tool.

This module provides command-line interface for managing documents,
including uploading, listing, and deleting documents.
"""

import argparse
import logging
import mimetypes
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import create_app, db
from app.models.document import (
    ALLOWED_EXTENSIONS,
    Document,
    allowed_file,
    get_file_extension,
    sanitize_filename,
)
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.submission import VALID_SUBMISSION_TYPES, Submission

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_upload_path(
    enrollment: Enrollment,
    filename: str,
    base_path: str = "uploads",
) -> str:
    """
    Generate organized upload path for a document.

    Path structure: uploads/{university_slug}/{semester}/{course_slug}/{StudentName}/

    Args:
        enrollment: Enrollment object containing course and student info
        filename: Sanitized filename
        base_path: Base upload directory

    Returns:
        Full file path for storage
    """
    course = enrollment.course
    student = enrollment.student
    university = course.university

    # Create path components
    university_slug = university.slug
    semester = course.semester
    course_slug = course.slug
    student_folder = f"{student.last_name}{student.first_name}"

    # Build path
    path = Path(base_path) / university_slug / semester / course_slug / student_folder
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
    enrollment_id: int,
    submission_type: str = "document",
    exam_id: int | None = None,
    notes: str | None = None,
) -> Submission | None:
    """
    Create a new submission record.

    Args:
        enrollment_id: Enrollment ID for this submission
        submission_type: Type of submission (document, assignment, etc.)
        exam_id: Optional exam ID if submission is for an exam
        notes: Optional notes about the submission

    Returns:
        Created Submission object or None if failed

    Raises:
        ValueError: If validation fails
    """
    # Validate enrollment exists
    enrollment = db.session.query(Enrollment).filter_by(id=enrollment_id).first()
    if not enrollment:
        raise ValueError(f"Enrollment with ID {enrollment_id} not found")

    # Validate submission type
    if submission_type not in VALID_SUBMISSION_TYPES:
        raise ValueError(
            f"Invalid submission type. Must be one of: {', '.join(VALID_SUBMISSION_TYPES)}"
        )

    # Validate exam if provided
    if exam_id:
        exam = db.session.query(Exam).filter_by(id=exam_id).first()
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
        db.session.add(submission)
        db.session.commit()

        logger.info(f"Created submission ID {submission.id} for enrollment {enrollment_id}")
        return submission

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while creating submission: {e}")
        return None


def upload_document(
    file_path: str,
    enrollment_id: int,
    submission_type: str = "document",
    exam_id: int | None = None,
    notes: str | None = None,
) -> Document | None:
    """
    Upload a document for a student enrollment.

    Args:
        file_path: Path to the file to upload
        enrollment_id: Enrollment ID for this document
        submission_type: Type of submission
        exam_id: Optional exam ID if document is for an exam
        notes: Optional notes about the submission

    Returns:
        Created Document object or None if failed

    Raises:
        ValueError: If validation fails
        FileNotFoundError: If source file doesn't exist
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
    enrollment = db.session.query(Enrollment).filter_by(id=enrollment_id).first()
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
        submission = create_submission(
            enrollment_id=enrollment_id,
            submission_type=submission_type,
            exam_id=exam_id,
            notes=notes,
        )
        if not submission:
            raise ValueError("Failed to create submission record")

        # Generate destination path
        dest_path = get_upload_path(enrollment, safe_filename)

        # Copy file to destination
        import shutil
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
        db.session.add(document)
        db.session.commit()

        logger.info(
            f"Uploaded document: {original_filename} -> {dest_path} "
            f"(submission ID: {submission.id})"
        )
        return document

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while uploading document: {e}")
        return None


def list_documents(
    enrollment_id: int | None = None,
    submission_id: int | None = None,
    file_type: str | None = None,
) -> list[Document]:
    """
    List documents with optional filters.

    Args:
        enrollment_id: Optional enrollment ID filter
        submission_id: Optional submission ID filter
        file_type: Optional file type filter

    Returns:
        List of Document objects matching the filters
    """
    try:
        query = db.session.query(Document).join(Submission)

        if enrollment_id:
            query = query.filter(Submission.enrollment_id == enrollment_id)

        if submission_id:
            query = query.filter(Document.submission_id == submission_id)

        if file_type:
            query = query.filter(Document.file_type == file_type.lower())

        documents = query.order_by(Document.upload_date.desc()).all()
        return documents

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing documents: {e}")
        return []


def get_document(document_id: int) -> Document | None:
    """
    Get a document by ID.

    Args:
        document_id: Document database ID

    Returns:
        Document object or None if not found
    """
    try:
        document = db.session.query(Document).filter_by(id=document_id).first()
        return document
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching document: {e}")
        return None


def delete_document(document_id: int, delete_file: bool = True) -> bool:
    """
    Delete a document from the database and optionally from disk.

    Args:
        document_id: Document database ID
        delete_file: Whether to delete the physical file (default: True)

    Returns:
        True if deleted successfully, False otherwise

    Raises:
        ValueError: If document not found
    """
    try:
        document = db.session.query(Document).filter_by(id=document_id).first()

        if not document:
            raise ValueError(f"Document with ID {document_id} not found")

        file_path = document.file_path
        document_name = document.original_filename

        # Delete database record
        db.session.delete(document)
        db.session.commit()

        # Delete physical file if requested
        if delete_file and file_path:
            try:
                Path(file_path).unlink(missing_ok=True)
                logger.info(f"Deleted file: {file_path}")
            except OSError as e:
                logger.warning(f"Could not delete file {file_path}: {e}")

        logger.info(f"Deleted document: {document_name}")
        return True

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while deleting document: {e}")
        return False


def list_submissions(
    enrollment_id: int | None = None,
    exam_id: int | None = None,
    status: str | None = None,
) -> list[Submission]:
    """
    List submissions with optional filters.

    Args:
        enrollment_id: Optional enrollment ID filter
        exam_id: Optional exam ID filter
        status: Optional status filter

    Returns:
        List of Submission objects matching the filters
    """
    try:
        query = db.session.query(Submission)

        if enrollment_id:
            query = query.filter_by(enrollment_id=enrollment_id)

        if exam_id:
            query = query.filter_by(exam_id=exam_id)

        if status:
            query = query.filter_by(status=status)

        submissions = query.order_by(Submission.submission_date.desc()).all()
        return submissions

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing submissions: {e}")
        return []


def update_submission_status(submission_id: int, status: str) -> Submission | None:
    """
    Update the status of a submission.

    Args:
        submission_id: Submission database ID
        status: New status value

    Returns:
        Updated Submission object or None if failed

    Raises:
        ValueError: If validation fails
    """
    from app.models.submission import VALID_SUBMISSION_STATUSES

    if status not in VALID_SUBMISSION_STATUSES:
        raise ValueError(
            f"Invalid status. Must be one of: {', '.join(VALID_SUBMISSION_STATUSES)}"
        )

    try:
        submission = db.session.query(Submission).filter_by(id=submission_id).first()

        if not submission:
            raise ValueError(f"Submission with ID {submission_id} not found")

        submission.status = status
        db.session.commit()

        logger.info(f"Updated submission {submission_id} status to: {status}")
        return submission

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while updating submission status: {e}")
        return None


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Document Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Upload document
    upload_parser = subparsers.add_parser("upload", help="Upload a document")
    upload_parser.add_argument("--file", required=True, help="Path to file to upload")
    upload_parser.add_argument(
        "--enrollment-id", type=int, required=True, help="Enrollment ID"
    )
    upload_parser.add_argument(
        "--type",
        default="document",
        choices=VALID_SUBMISSION_TYPES,
        help="Submission type",
    )
    upload_parser.add_argument("--exam-id", type=int, help="Optional exam ID")
    upload_parser.add_argument("--notes", help="Optional notes")

    # List documents
    list_parser = subparsers.add_parser("list", help="List documents")
    list_parser.add_argument("--enrollment-id", type=int, help="Filter by enrollment")
    list_parser.add_argument("--submission-id", type=int, help="Filter by submission")
    list_parser.add_argument("--file-type", help="Filter by file type (e.g., pdf)")

    # Show document
    show_parser = subparsers.add_parser("show", help="Show document details")
    show_parser.add_argument("document_id", type=int, help="Document ID")

    # Delete document
    delete_parser = subparsers.add_parser("delete", help="Delete a document")
    delete_parser.add_argument("document_id", type=int, help="Document ID")
    delete_parser.add_argument("--yes", action="store_true", help="Skip confirmation")
    delete_parser.add_argument(
        "--keep-file", action="store_true", help="Keep the physical file"
    )

    # List submissions
    submissions_parser = subparsers.add_parser(
        "submissions", help="List submissions"
    )
    submissions_parser.add_argument(
        "--enrollment-id", type=int, help="Filter by enrollment"
    )
    submissions_parser.add_argument("--exam-id", type=int, help="Filter by exam")
    submissions_parser.add_argument("--status", help="Filter by status")

    # Update submission status
    status_parser = subparsers.add_parser(
        "update-status", help="Update submission status"
    )
    status_parser.add_argument("submission_id", type=int, help="Submission ID")
    status_parser.add_argument(
        "--status",
        required=True,
        choices=["submitted", "reviewed", "graded", "returned"],
        help="New status",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create app and initialize database connection
    app = create_app()
    with app.app_context():
        try:
            if args.command == "upload":
                document = upload_document(
                    file_path=args.file,
                    enrollment_id=args.enrollment_id,
                    submission_type=args.type,
                    exam_id=args.exam_id,
                    notes=args.notes,
                )
                if document:
                    print("\nDocument uploaded successfully!")
                    print(f"ID: {document.id}")
                    print(f"Filename: {document.filename}")
                    print(f"Original: {document.original_filename}")
                    print(f"Path: {document.file_path}")
                    print(f"Type: {document.file_type}")
                    print(f"Size: {document.file_size_human}")
                    print(f"Submission ID: {document.submission_id}")
                    return 0
                print("Error: Failed to upload document")
                return 1

            if args.command == "list":
                documents = list_documents(
                    enrollment_id=args.enrollment_id,
                    submission_id=args.submission_id,
                    file_type=args.file_type,
                )
                if not documents:
                    print("No documents found")
                    return 0

                print(f"\nFound {len(documents)} document(s):\n")
                for doc in documents:
                    print(f"ID {doc.id}: {doc.original_filename}")
                    print(f"  Path: {doc.file_path}")
                    print(f"  Type: {doc.file_type}")
                    print(f"  Size: {doc.file_size_human}")
                    print(f"  Uploaded: {doc.upload_date}")
                    print()
                return 0

            if args.command == "show":
                document = get_document(args.document_id)
                if not document:
                    print(f"Error: Document with ID {args.document_id} not found")
                    return 1

                print("\nDocument Details:")
                print(f"ID: {document.id}")
                print(f"Filename: {document.filename}")
                print(f"Original filename: {document.original_filename}")
                print(f"Path: {document.file_path}")
                print(f"Type: {document.file_type}")
                print(f"Size: {document.file_size_human} ({document.file_size} bytes)")
                print(f"MIME type: {document.mime_type}")
                print(f"Submission ID: {document.submission_id}")
                print(f"Uploaded: {document.upload_date}")
                print(f"Created: {document.created_at}")
                print(f"Updated: {document.updated_at}")
                return 0

            if args.command == "delete":
                document = get_document(args.document_id)
                if not document:
                    print(f"Error: Document with ID {args.document_id} not found")
                    return 1

                if not args.yes:
                    print("\nAre you sure you want to delete this document?")
                    print(f"Filename: {document.original_filename}")
                    print(f"Path: {document.file_path}")
                    response = input("\nType 'yes' to confirm: ")
                    if response.lower() != "yes":
                        print("Deletion cancelled")
                        return 0

                if delete_document(args.document_id, delete_file=not args.keep_file):
                    print("Document deleted successfully")
                    return 0
                print("Error: Failed to delete document")
                return 1

            if args.command == "submissions":
                submissions = list_submissions(
                    enrollment_id=args.enrollment_id,
                    exam_id=args.exam_id,
                    status=args.status,
                )
                if not submissions:
                    print("No submissions found")
                    return 0

                print(f"\nFound {len(submissions)} submission(s):\n")
                for sub in submissions:
                    # Pre-fetch related data to avoid detached instance issues
                    student_name = f"{sub.enrollment.student.first_name} {sub.enrollment.student.last_name}"
                    course_name = sub.enrollment.course.name
                    doc_count = sub.documents.count()

                    print(f"ID {sub.id}: {sub.submission_type}")
                    print(f"  Student: {student_name}")
                    print(f"  Course: {course_name}")
                    print(f"  Status: {sub.status}")
                    print(f"  Documents: {doc_count}")
                    print(f"  Submitted: {sub.submission_date}")
                    if sub.notes:
                        print(f"  Notes: {sub.notes}")
                    print()
                return 0

            if args.command == "update-status":
                submission = update_submission_status(
                    submission_id=args.submission_id,
                    status=args.status,
                )
                if submission:
                    print("\nSubmission status updated successfully!")
                    print(f"ID: {submission.id}")
                    print(f"Status: {submission.status}")
                    return 0
                print("Error: Failed to update submission status")
                return 1

        except ValueError as e:
            print(f"Validation error: {e}")
            return 1
        except FileNotFoundError as e:
            print(f"File error: {e}")
            return 1
        except IntegrityError as e:
            print(f"Database constraint error: {e}")
            return 1
        except Exception as e:
            logger.exception("Unexpected error")
            print(f"Unexpected error: {e}")
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
