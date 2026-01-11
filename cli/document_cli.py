"""
Document management CLI tool.

This module provides command-line interface for managing documents,
including uploading, listing, and deleting documents.
"""

import argparse
import logging
import sys

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import create_app
from app.models.submission import VALID_SUBMISSION_TYPES
from app.services.document_service import DocumentService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
    submissions_parser = subparsers.add_parser("submissions", help="List submissions")
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
        service = DocumentService()

        try:
            if args.command == "upload":
                document = service.upload_document(
                    file_path=args.file,
                    enrollment_id=args.enrollment_id,
                    submission_type=args.type,
                    exam_id=args.exam_id,
                    notes=args.notes,
                )
                print("\nDocument uploaded successfully!")
                print(f"ID: {document.id}")
                print(f"Filename: {document.filename}")
                print(f"Original: {document.original_filename}")
                print(f"Path: {document.file_path}")
                print(f"Type: {document.file_type}")
                print(f"Size: {document.file_size_human}")
                print(f"Submission ID: {document.submission_id}")
                return 0

            if args.command == "list":
                documents = service.list_documents(
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
                document = service.get_document(args.document_id)
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
                document = service.get_document(args.document_id)

                if not args.yes:
                    print("\nAre you sure you want to delete this document?")
                    print(f"Filename: {document.original_filename}")
                    print(f"Path: {document.file_path}")
                    response = input("\nType 'yes' to confirm: ")
                    if response.lower() != "yes":
                        print("Deletion cancelled")
                        return 0

                service.delete_document(
                    args.document_id, delete_file=not args.keep_file
                )
                print("Document deleted successfully")
                return 0

            if args.command == "submissions":
                submissions = service.list_submissions(
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
                submission = service.update_submission_status(
                    submission_id=args.submission_id,
                    status=args.status,
                )
                print("\nSubmission status updated successfully!")
                print(f"ID: {submission.id}")
                print(f"Status: {submission.status}")
                return 0

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

        except FileNotFoundError as e:
            logger.error(f"File error: {e}")
            print(f"File error: {e}", file=sys.stderr)
            return 1

        except IntegrityError as e:
            logger.error(f"Database constraint error: {e}")
            print(
                "Database constraint error. Please check your input.", file=sys.stderr
            )
            return 1

        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}", exc_info=True)
            print("Database error. Please try again.", file=sys.stderr)
            return 1

        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            print("\nOperation cancelled.", file=sys.stderr)
            return 130

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
