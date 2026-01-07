"""
Email import CLI tool.

This module provides command-line interface for importing documents from
email files (.eml, .mbox) and matching attachments to students.
"""

import argparse
import email
import logging
import mailbox
import os
import re
import sys
from datetime import UTC, datetime
from email.header import decode_header
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from app import create_app, db
from app.models.course import Course
from app.models.document import (
    Document,
    allowed_file,
    get_file_extension,
    sanitize_filename,
)
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.submission import Submission

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def decode_email_header(header: str) -> str:
    """
    Decode an email header handling various encodings.

    Args:
        header: Raw email header string

    Returns:
        Decoded header string
    """
    if not header:
        return ""

    decoded_parts = []
    for part, encoding in decode_header(header):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
            except (UnicodeDecodeError, LookupError):
                decoded_parts.append(part.decode("utf-8", errors="replace"))
        else:
            decoded_parts.append(part)

    return " ".join(decoded_parts)


def extract_email_address(from_header: str) -> str:
    """
    Extract email address from From header.

    Args:
        from_header: Email From header

    Returns:
        Extracted email address
    """
    # Try to find email in angle brackets
    match = re.search(r"<([^>]+)>", from_header)
    if match:
        return match.group(1).lower()

    # Try to find bare email
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", from_header)
    if match:
        return match.group(0).lower()

    return from_header.lower()


def extract_student_id_from_text(text: str) -> str | None:
    """
    Extract student ID (Matrikelnummer) from text.

    Looks for 8-digit numbers that could be student IDs.

    Args:
        text: Text to search

    Returns:
        Student ID if found, None otherwise
    """
    # Look for 8-digit numbers (common format for Matrikelnummer)
    matches = re.findall(r"\b\d{8}\b", text)
    if matches:
        return matches[0]
    return None


def match_student_by_email(
    email_address: str, course_id: int | None = None
) -> Enrollment | None:
    """
    Try to match a student by their email address.

    Args:
        email_address: Email address to match
        course_id: Optional course ID to filter enrollments

    Returns:
        Matching Enrollment or None
    """
    query = (
        db.session.query(Enrollment)
        .join(Student)
        .filter(Student.email == email_address)
        .filter(Enrollment.status == "active")
    )

    if course_id:
        query = query.filter(Enrollment.course_id == course_id)

    return query.first()


def match_student_by_id(
    student_id: str, course_id: int | None = None
) -> Enrollment | None:
    """
    Try to match a student by their student ID.

    Args:
        student_id: Student ID to match
        course_id: Optional course ID to filter enrollments

    Returns:
        Matching Enrollment or None
    """
    query = (
        db.session.query(Enrollment)
        .join(Student)
        .filter(Student.student_id == student_id)
        .filter(Enrollment.status == "active")
    )

    if course_id:
        query = query.filter(Enrollment.course_id == course_id)

    return query.first()


def match_student_by_name(name: str, course_id: int | None = None) -> Enrollment | None:
    """
    Try to match a student by name using fuzzy matching.

    Args:
        name: Name to match (can be "First Last" or "Last, First")
        course_id: Optional course ID to filter enrollments

    Returns:
        Matching Enrollment or None
    """
    # Normalize the name
    name_parts = re.split(r"[,\s]+", name.strip())
    name_parts = [p.lower() for p in name_parts if p]

    if not name_parts:
        return None

    # Get all active enrollments
    query = (
        db.session.query(Enrollment).join(Student).filter(Enrollment.status == "active")
    )

    if course_id:
        query = query.filter(Enrollment.course_id == course_id)

    enrollments = query.all()

    for enrollment in enrollments:
        student = enrollment.student
        student_first = student.first_name.lower()
        student_last = student.last_name.lower()

        # Check various combinations
        if len(name_parts) >= 2:
            # "First Last" format
            if name_parts[0] == student_first and name_parts[1] == student_last:
                return enrollment
            # "Last First" format
            if name_parts[0] == student_last and name_parts[1] == student_first:
                return enrollment
            # "Last, First" format (after splitting by comma)
            if name_parts[0] == student_last and name_parts[-1] == student_first:
                return enrollment

        # Single name part - check if it matches either first or last
        if len(name_parts) == 1:
            if name_parts[0] == student_first or name_parts[0] == student_last:
                return enrollment

    return None


def get_upload_path(
    enrollment: Enrollment, filename: str, base_path: str = "uploads"
) -> str:
    """
    Generate organized upload path for a document.

    Args:
        enrollment: Enrollment object
        filename: Sanitized filename
        base_path: Base upload directory

    Returns:
        Full file path for storage
    """
    course = enrollment.course
    student = enrollment.student
    university = course.university

    path = (
        Path(base_path)
        / university.slug
        / course.semester
        / course.slug
        / f"{student.last_name}{student.first_name}"
    )
    path.mkdir(parents=True, exist_ok=True)

    final_path = path / filename
    counter = 1
    while final_path.exists():
        name, ext = os.path.splitext(filename)
        final_path = path / f"{name}_{counter}{ext}"
        counter += 1

    return str(final_path)


def process_attachment(
    attachment: email.message.Message,
    enrollment: Enrollment,
    email_subject: str,
    email_date: datetime,
) -> Document | None:
    """
    Process an email attachment and save it.

    Args:
        attachment: Email attachment message part
        enrollment: Matched enrollment for the student
        email_subject: Email subject for notes
        email_date: Email date

    Returns:
        Created Document or None if failed
    """
    filename = attachment.get_filename()
    if not filename:
        return None

    # Decode filename if needed
    filename = decode_email_header(filename)

    if not allowed_file(filename):
        logger.warning(f"Skipping unsupported file type: {filename}")
        return None

    # Get content
    content = attachment.get_payload(decode=True)
    if not content:
        return None

    # Sanitize filename
    safe_filename = sanitize_filename(filename)

    try:
        # Generate path and save file
        file_path = get_upload_path(enrollment, safe_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        # Get file info
        file_size = len(content)
        file_type = get_file_extension(filename)
        mime_type = attachment.get_content_type()

        # Create submission
        submission = Submission(
            enrollment_id=enrollment.id,
            submission_type="email_attachment",
            notes=f"Importiert aus E-Mail: {email_subject}",
            submission_date=email_date or datetime.now(UTC),
            status="submitted",
        )
        db.session.add(submission)
        db.session.flush()

        # Create document
        document = Document(
            submission_id=submission.id,
            filename=safe_filename,
            original_filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            mime_type=mime_type,
            upload_date=datetime.now(UTC),
        )
        db.session.add(document)

        logger.info(
            f"Saved attachment: {filename} for student {enrollment.student.last_name}"
        )
        return document

    except OSError as e:
        logger.error(f"File I/O error processing attachment {filename}: {e}")
        return None

    except SQLAlchemyError as e:
        logger.error(
            f"Database error processing attachment {filename}: {e}", exc_info=True
        )
        db.session.rollback()
        return None

    except Exception as e:
        logger.error(
            f"Unexpected error processing attachment {filename}: {e}", exc_info=True
        )
        return None


def process_email_message(
    msg: email.message.Message,
    course_id: int | None = None,
) -> dict:
    """
    Process a single email message and extract attachments.

    Args:
        msg: Email message object
        course_id: Optional course ID to filter student matches

    Returns:
        Dictionary with processing results
    """
    result = {
        "subject": "",
        "from": "",
        "date": None,
        "matched_student": None,
        "attachments": [],
        "errors": [],
    }

    # Extract headers
    subject = decode_email_header(msg.get("Subject", ""))
    from_header = decode_email_header(msg.get("From", ""))
    date_str = msg.get("Date", "")

    result["subject"] = subject
    result["from"] = from_header

    # Parse date
    if date_str:
        try:
            result["date"] = email.utils.parsedate_to_datetime(date_str)
        except (ValueError, TypeError):
            result["date"] = datetime.now(UTC)
    else:
        result["date"] = datetime.now(UTC)

    # Try to match student
    enrollment = None

    # 1. Try matching by email
    email_address = extract_email_address(from_header)
    if email_address:
        enrollment = match_student_by_email(email_address, course_id)

    # 2. Try matching by student ID in subject or body
    if not enrollment:
        body_text = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode("utf-8", errors="replace")
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body_text = payload.decode("utf-8", errors="replace")

        student_id = extract_student_id_from_text(subject + " " + body_text)
        if student_id:
            enrollment = match_student_by_id(student_id, course_id)

    # 3. Try matching by name from From header
    if not enrollment:
        # Extract name part from "Name <email>" format
        name_match = re.match(r"^([^<]+)", from_header)
        if name_match:
            name = name_match.group(1).strip().strip('"')
            enrollment = match_student_by_name(name, course_id)

    if enrollment:
        result["matched_student"] = {
            "id": enrollment.student.id,
            "name": f"{enrollment.student.first_name} {enrollment.student.last_name}",
            "email": enrollment.student.email,
        }

        # Process attachments
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    doc = process_attachment(
                        part,
                        enrollment,
                        subject,
                        result["date"],
                    )
                    if doc:
                        result["attachments"].append(
                            {
                                "filename": doc.original_filename,
                                "size": doc.file_size,
                                "document_id": doc.id,
                            }
                        )
    else:
        result["errors"].append("Could not match email to any enrolled student")

    return result


def parse_eml_file(file_path: str, course_id: int | None = None) -> list[dict]:
    """
    Parse an .eml file and process it.

    Args:
        file_path: Path to .eml file
        course_id: Optional course ID to filter student matches

    Returns:
        List of processing results
    """
    results = []

    try:
        with open(file_path, "rb") as f:
            msg = email.message_from_binary_file(f)
            result = process_email_message(msg, course_id)
            result["source_file"] = file_path
            results.append(result)
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}: {e}")
        results.append(
            {
                "source_file": file_path,
                "errors": [f"File not found: {e}"],
            }
        )
    except OSError as e:
        logger.error(f"File I/O error parsing {file_path}: {e}")
        results.append(
            {
                "source_file": file_path,
                "errors": [f"File I/O error: {e}"],
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error parsing {file_path}: {e}", exc_info=True)
        results.append(
            {
                "source_file": file_path,
                "errors": [str(e)],
            }
        )

    return results


def parse_mbox_file(file_path: str, course_id: int | None = None) -> list[dict]:
    """
    Parse an .mbox file and process all messages.

    Args:
        file_path: Path to .mbox file
        course_id: Optional course ID to filter student matches

    Returns:
        List of processing results
    """
    results = []

    try:
        mbox = mailbox.mbox(file_path)
        for i, msg in enumerate(mbox):
            result = process_email_message(msg, course_id)
            result["source_file"] = f"{file_path}:message_{i}"
            results.append(result)
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}: {e}")
        results.append(
            {
                "source_file": file_path,
                "errors": [f"File not found: {e}"],
            }
        )
    except OSError as e:
        logger.error(f"File I/O error parsing mbox {file_path}: {e}")
        results.append(
            {
                "source_file": file_path,
                "errors": [f"File I/O error: {e}"],
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error parsing mbox {file_path}: {e}", exc_info=True)
        results.append(
            {
                "source_file": file_path,
                "errors": [str(e)],
            }
        )

    return results


def import_emails(
    file_path: str,
    course_id: int | None = None,
) -> dict:
    """
    Import documents from email file(s).

    Args:
        file_path: Path to email file (.eml or .mbox) or directory
        course_id: Optional course ID to filter student matches

    Returns:
        Dictionary with import summary
    """
    summary = {
        "files_processed": 0,
        "emails_processed": 0,
        "attachments_saved": 0,
        "students_matched": 0,
        "unmatched_emails": 0,
        "errors": [],
        "details": [],
    }

    path = Path(file_path)

    if path.is_file():
        files_to_process = [path]
    elif path.is_dir():
        files_to_process = list(path.glob("*.eml")) + list(path.glob("*.mbox"))
    else:
        summary["errors"].append(f"Path not found: {file_path}")
        return summary

    for file_path in files_to_process:
        summary["files_processed"] += 1

        ext = file_path.suffix.lower()
        if ext == ".eml":
            results = parse_eml_file(str(file_path), course_id)
        elif ext == ".mbox":
            results = parse_mbox_file(str(file_path), course_id)
        else:
            summary["errors"].append(f"Unsupported file type: {file_path}")
            continue

        for result in results:
            summary["emails_processed"] += 1
            summary["details"].append(result)

            if result.get("matched_student"):
                summary["students_matched"] += 1
                summary["attachments_saved"] += len(result.get("attachments", []))
            else:
                summary["unmatched_emails"] += 1

            if result.get("errors"):
                summary["errors"].extend(result["errors"])

    return summary


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Email Import CLI - Import documents from email files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import emails from file(s)")
    import_parser.add_argument(
        "path",
        help="Path to .eml file, .mbox file, or directory containing email files",
    )
    import_parser.add_argument(
        "--course-id",
        type=int,
        help="Filter student matches to specific course",
    )
    import_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse emails but don't save attachments",
    )

    # Parse single file command
    parse_parser = subparsers.add_parser("parse", help="Parse email file and show info")
    parse_parser.add_argument("file", help="Path to .eml or .mbox file")

    # List courses command (for reference)
    subparsers.add_parser("list-courses", help="List available courses")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create app and initialize database connection
    app = create_app()
    with app.app_context():
        try:
            if args.command == "import":
                print(f"\nImporting emails from: {args.path}")
                if args.course_id:
                    course = (
                        db.session.query(Course).filter_by(id=args.course_id).first()
                    )
                    if not course:
                        print(f"Error: Course with ID {args.course_id} not found")
                        return 1
                    print(f"Filtering to course: {course.name}")

                summary = import_emails(args.path, args.course_id)

                if not args.dry_run:
                    db.session.commit()

                print("\n" + "=" * 50)
                print("IMPORT SUMMARY")
                print("=" * 50)
                print(f"Files processed:      {summary['files_processed']}")
                print(f"Emails processed:     {summary['emails_processed']}")
                print(f"Students matched:     {summary['students_matched']}")
                print(f"Attachments saved:    {summary['attachments_saved']}")
                print(f"Unmatched emails:     {summary['unmatched_emails']}")

                if summary["errors"]:
                    print(f"\nErrors ({len(summary['errors'])}):")
                    for error in summary["errors"][:10]:
                        print(f"  - {error}")
                    if len(summary["errors"]) > 10:
                        print(f"  ... and {len(summary['errors']) - 10} more")

                return 0

            if args.command == "parse":
                path = Path(args.file)
                if not path.exists():
                    print(f"Error: File not found: {args.file}")
                    return 1

                ext = path.suffix.lower()
                if ext == ".eml":
                    results = parse_eml_file(args.file)
                elif ext == ".mbox":
                    results = parse_mbox_file(args.file)
                else:
                    print(f"Error: Unsupported file type: {ext}")
                    return 1

                print(f"\nParsed {len(results)} email(s):\n")
                for i, result in enumerate(results):
                    print(f"Email {i + 1}:")
                    print(f"  Subject: {result.get('subject', 'N/A')}")
                    print(f"  From: {result.get('from', 'N/A')}")
                    print(f"  Date: {result.get('date', 'N/A')}")
                    if result.get("matched_student"):
                        print(f"  Matched Student: {result['matched_student']['name']}")
                    else:
                        print("  Matched Student: None")
                    print()

                return 0

            if args.command == "list-courses":
                courses = db.session.query(Course).order_by(Course.name).all()
                if not courses:
                    print("No courses found")
                    return 0

                print(f"\nFound {len(courses)} course(s):\n")
                for course in courses:
                    enrollments = Enrollment.query.filter_by(
                        course_id=course.id, status="active"
                    ).count()
                    print(f"ID {course.id}: {course.name}")
                    print(f"  Semester: {course.semester}")
                    print(f"  University: {course.university.name}")
                    print(f"  Active enrollments: {enrollments}")
                    print()
                return 0

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

        except SQLAlchemyError as e:
            db.session.rollback()
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
