"""
Document routes blueprint.

This module provides web routes for managing documents through the Flask interface.
"""

import logging
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from app import db
from app.forms.document import (
    BulkDocumentUploadForm,
    DocumentSearchForm,
    DocumentUploadForm,
    SubmissionStatusForm,
)
from app.models.course import Course
from app.models.document import (
    Document,
    allowed_file,
    get_file_extension,
    sanitize_filename,
)
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.student import Student
from app.models.submission import Submission

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("document", __name__, url_prefix="/documents")


def get_upload_path(enrollment: Enrollment, filename: str) -> str:
    """
    Generate organized upload path for a document.

    Path structure: uploads/{university_slug}/{semester}/{course_slug}/{StudentName}/

    Args:
        enrollment: Enrollment object containing course and student info
        filename: Sanitized filename

    Returns:
        Full file path for storage
    """
    course = enrollment.course
    student = enrollment.student
    university = course.university

    # Create path components
    base_path = current_app.config.get("UPLOAD_FOLDER", "uploads")
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


@bp.route("/")
def index() -> str:
    """
    List all documents with search and filter capabilities.

    Query parameters:
        course_id: Optional course filter
        student_id: Optional student filter
        file_type: Optional file type filter
        status: Optional submission status filter

    Returns:
        Rendered template with list of documents
    """
    form = DocumentSearchForm(request.args)

    try:
        # Build query
        query = (
            db.session.query(Document)
            .join(Submission)
            .join(Enrollment)
            .join(Student)
            .join(Course)
        )

        # Apply filters
        course_id = request.args.get("course_id", type=int)
        student_id = request.args.get("student_id", type=int)
        file_type = request.args.get("file_type", "").strip()
        status = request.args.get("status", "").strip()

        if course_id:
            query = query.filter(Course.id == course_id)

        if student_id:
            query = query.filter(Student.id == student_id)

        if file_type:
            query = query.filter(Document.file_type == file_type.lower())

        if status:
            query = query.filter(Submission.status == status)

        documents = query.order_by(Document.upload_date.desc()).all()

        # Get filter options
        courses = db.session.query(Course).order_by(Course.name).all()
        students = db.session.query(Student).order_by(Student.last_name).all()

        # Populate form choices
        form.course_id.choices = [("", "-- Alle Kurse --")] + [
            (c.id, c.name) for c in courses
        ]
        form.student_id.choices = [("", "-- Alle Studierende --")] + [
            (s.id, f"{s.last_name}, {s.first_name}") for s in students
        ]

        return render_template(
            "document/list.html",
            documents=documents,
            form=form,
            courses=courses,
            students=students,
        )

    except SQLAlchemyError as e:
        logger.error(f"Error while listing documents: {e}")
        flash("Fehler beim Laden der Dokumente.", "error")
        return render_template(
            "document/list.html",
            documents=[],
            form=form,
            courses=[],
            students=[],
        )


@bp.route("/<int:document_id>")
def show(document_id: int) -> str | Any:
    """
    Show details for a specific document.

    Args:
        document_id: Document database ID

    Returns:
        Rendered template with document details or redirect
    """
    try:
        document = db.session.query(Document).filter_by(id=document_id).first()

        if not document:
            flash(f"Dokument mit ID {document_id} nicht gefunden.", "error")
            return redirect(url_for("document.index"))

        return render_template("document/detail.html", document=document)

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching document: {e}")
        flash("Fehler beim Laden des Dokuments.", "error")
        return redirect(url_for("document.index"))


@bp.route("/<int:document_id>/download")
def download(document_id: int) -> Any:
    """
    Download a document.

    Args:
        document_id: Document database ID

    Returns:
        File download response or redirect on error
    """
    try:
        document = db.session.query(Document).filter_by(id=document_id).first()

        if not document:
            flash(f"Dokument mit ID {document_id} nicht gefunden.", "error")
            return redirect(url_for("document.index"))

        file_path = Path(document.file_path)
        if not file_path.exists():
            flash("Datei nicht gefunden auf dem Server.", "error")
            return redirect(url_for("document.show", document_id=document_id))

        return send_file(
            file_path,
            as_attachment=True,
            download_name=document.original_filename,
            mimetype=document.mime_type,
        )

    except Exception as e:
        logger.error(f"Error while downloading document: {e}")
        flash("Fehler beim Herunterladen der Datei.", "error")
        return redirect(url_for("document.index"))


@bp.route("/upload", methods=["GET", "POST"])
def upload() -> str | Any:
    """
    Upload a new document.

    GET: Show upload form
    POST: Process upload and redirect to document detail

    Returns:
        Rendered form template (GET) or redirect (POST)
    """
    try:
        # Get available enrollments and exams for form choices
        enrollments = (
            db.session.query(Enrollment)
            .join(Student)
            .join(Course)
            .filter(Enrollment.status == "active")
            .order_by(Student.last_name, Course.name)
            .all()
        )

        exams = db.session.query(Exam).order_by(Exam.exam_date.desc()).all()

        form = DocumentUploadForm()
        form.enrollment_id.choices = [
            (
                e.id,
                f"{e.student.last_name}, {e.student.first_name} - {e.course.name}",
            )
            for e in enrollments
        ]
        form.exam_id.choices = [("", "-- Keine Prüfung --")] + [
            (ex.id, f"{ex.name} ({ex.course.name})") for ex in exams
        ]

        if form.validate_on_submit():
            file = form.file.data
            original_filename = secure_filename(file.filename)

            if not allowed_file(original_filename):
                flash("Dateityp nicht erlaubt.", "error")
                return render_template("document/upload.html", form=form)

            # Get enrollment
            enrollment = (
                db.session.query(Enrollment)
                .filter_by(id=form.enrollment_id.data)
                .first()
            )

            if not enrollment:
                flash("Einschreibung nicht gefunden.", "error")
                return render_template("document/upload.html", form=form)

            # Sanitize filename and generate path
            safe_filename = sanitize_filename(original_filename)
            file_path = get_upload_path(enrollment, safe_filename)

            # Save file
            file.save(file_path)

            # Get file info
            file_size = os.path.getsize(file_path)
            file_type = get_file_extension(original_filename)
            mime_type, _ = mimetypes.guess_type(original_filename)

            # Create submission
            submission = Submission(
                enrollment_id=form.enrollment_id.data,
                submission_type=form.submission_type.data,
                exam_id=form.exam_id.data if form.exam_id.data else None,
                notes=form.notes.data if form.notes.data else None,
                submission_date=datetime.now(timezone.utc),
                status="submitted",
            )
            db.session.add(submission)
            db.session.flush()  # Get submission ID

            # Create document record
            document = Document(
                submission_id=submission.id,
                filename=safe_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                mime_type=mime_type,
                upload_date=datetime.now(timezone.utc),
            )
            db.session.add(document)
            db.session.commit()

            logger.info(f"Uploaded document: {original_filename} -> {file_path}")
            flash(f"Dokument '{original_filename}' erfolgreich hochgeladen.", "success")
            return redirect(url_for("document.show", document_id=document.id))

        # Show form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("document/upload.html", form=form)

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while uploading document: {e}")
        flash("Datenbankfehler beim Hochladen.", "error")
        return redirect(url_for("document.index"))


@bp.route("/bulk-upload", methods=["GET", "POST"])
def bulk_upload() -> str | Any:
    """
    Upload multiple documents at once.

    GET: Show bulk upload form
    POST: Process uploads and show results

    Returns:
        Rendered form template (GET) or results page (POST)
    """
    try:
        courses = db.session.query(Course).order_by(Course.name).all()
        exams = db.session.query(Exam).order_by(Exam.exam_date.desc()).all()

        form = BulkDocumentUploadForm()
        form.course_id.choices = [(c.id, c.name) for c in courses]
        form.exam_id.choices = [("", "-- Keine Prüfung --")] + [
            (ex.id, f"{ex.name} ({ex.course.name})") for ex in exams
        ]

        if form.validate_on_submit():
            files = request.files.getlist("files")
            course_id = form.course_id.data
            submission_type = form.submission_type.data
            exam_id = form.exam_id.data if form.exam_id.data else None
            notes = form.notes.data

            results = {"success": [], "failed": [], "unmatched": []}

            for file in files:
                if not file or not file.filename:
                    continue

                original_filename = secure_filename(file.filename)

                if not allowed_file(original_filename):
                    results["failed"].append(
                        {"filename": original_filename, "reason": "Dateityp nicht erlaubt"}
                    )
                    continue

                # Try to match file to student based on filename
                # Expected format: LastnameFirstname.pdf or Lastname_Firstname.pdf
                matched_enrollment = match_file_to_enrollment(
                    original_filename, course_id
                )

                if not matched_enrollment:
                    results["unmatched"].append(original_filename)
                    continue

                try:
                    # Sanitize and save file
                    safe_filename = sanitize_filename(original_filename)
                    file_path = get_upload_path(matched_enrollment, safe_filename)
                    file.save(file_path)

                    # Get file info
                    file_size = os.path.getsize(file_path)
                    file_type = get_file_extension(original_filename)
                    mime_type, _ = mimetypes.guess_type(original_filename)

                    # Create submission
                    submission = Submission(
                        enrollment_id=matched_enrollment.id,
                        submission_type=submission_type,
                        exam_id=exam_id,
                        notes=notes,
                        submission_date=datetime.now(timezone.utc),
                        status="submitted",
                    )
                    db.session.add(submission)
                    db.session.flush()

                    # Create document
                    document = Document(
                        submission_id=submission.id,
                        filename=safe_filename,
                        original_filename=original_filename,
                        file_path=file_path,
                        file_type=file_type,
                        file_size=file_size,
                        mime_type=mime_type,
                        upload_date=datetime.now(timezone.utc),
                    )
                    db.session.add(document)

                    results["success"].append(
                        {
                            "filename": original_filename,
                            "student": f"{matched_enrollment.student.last_name}, {matched_enrollment.student.first_name}",
                        }
                    )

                except Exception as e:
                    logger.error(f"Error uploading {original_filename}: {e}")
                    results["failed"].append(
                        {"filename": original_filename, "reason": str(e)}
                    )

            db.session.commit()

            return render_template(
                "document/bulk_results.html",
                results=results,
                total=len(files),
            )

        # Show form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("document/bulk_upload.html", form=form, courses=courses)

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error during bulk upload: {e}")
        flash("Datenbankfehler beim Hochladen.", "error")
        return redirect(url_for("document.index"))


def match_file_to_enrollment(filename: str, course_id: int) -> Enrollment | None:
    """
    Try to match a filename to a student enrollment.

    Attempts to extract student name from filename and match to enrollment.

    Args:
        filename: Original filename
        course_id: Course ID to search enrollments

    Returns:
        Matching Enrollment or None if no match found
    """
    import re

    # Remove extension
    name_part = os.path.splitext(filename)[0]

    # Try different patterns
    # Pattern 1: LastnameFirstname (e.g., MuellerMax.pdf)
    # Pattern 2: Lastname_Firstname (e.g., Mueller_Max.pdf)
    # Pattern 3: Lastname-Firstname (e.g., Mueller-Max.pdf)

    # Normalize separators
    name_part = re.sub(r"[-_\s]+", "", name_part)

    # Get all enrollments for the course
    enrollments = (
        db.session.query(Enrollment)
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


@bp.route("/<int:document_id>/delete", methods=["GET", "POST"])
def delete(document_id: int) -> str | Any:
    """
    Delete a document.

    GET: Show confirmation page
    POST: Delete document and redirect to list

    Args:
        document_id: Document database ID

    Returns:
        Rendered confirmation template (GET) or redirect (POST)
    """
    try:
        document = db.session.query(Document).filter_by(id=document_id).first()

        if not document:
            flash(f"Dokument mit ID {document_id} nicht gefunden.", "error")
            return redirect(url_for("document.index"))

        if request.method == "GET":
            return render_template("document/delete.html", document=document)

        # POST: Delete document
        file_path = document.file_path
        document_name = document.original_filename

        db.session.delete(document)
        db.session.commit()

        # Delete physical file
        try:
            Path(file_path).unlink(missing_ok=True)
        except OSError as e:
            logger.warning(f"Could not delete file {file_path}: {e}")

        flash(f"Dokument '{document_name}' erfolgreich gelöscht.", "success")
        return redirect(url_for("document.index"))

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while deleting document: {e}")
        flash("Fehler beim Löschen des Dokuments.", "error")
        return redirect(url_for("document.show", document_id=document_id))


# Submission routes


@bp.route("/submissions")
def submissions() -> str:
    """
    List all submissions.

    Query parameters:
        course_id: Optional course filter
        status: Optional status filter

    Returns:
        Rendered template with list of submissions
    """
    try:
        query = db.session.query(Submission).join(Enrollment).join(Course)

        course_id = request.args.get("course_id", type=int)
        status = request.args.get("status", "").strip()

        if course_id:
            query = query.filter(Course.id == course_id)

        if status:
            query = query.filter(Submission.status == status)

        submissions_list = query.order_by(Submission.submission_date.desc()).all()

        courses = db.session.query(Course).order_by(Course.name).all()

        return render_template(
            "document/submissions.html",
            submissions=submissions_list,
            courses=courses,
            course_id=course_id,
            status=status,
        )

    except SQLAlchemyError as e:
        logger.error(f"Error while listing submissions: {e}")
        flash("Fehler beim Laden der Einreichungen.", "error")
        return render_template(
            "document/submissions.html",
            submissions=[],
            courses=[],
            course_id=None,
            status="",
        )


@bp.route("/submissions/<int:submission_id>")
def submission_detail(submission_id: int) -> str | Any:
    """
    Show details for a specific submission.

    Args:
        submission_id: Submission database ID

    Returns:
        Rendered template with submission details or redirect
    """
    try:
        submission = db.session.query(Submission).filter_by(id=submission_id).first()

        if not submission:
            flash(f"Einreichung mit ID {submission_id} nicht gefunden.", "error")
            return redirect(url_for("document.submissions"))

        documents = submission.documents.all()
        form = SubmissionStatusForm(obj=submission)

        return render_template(
            "document/submission_detail.html",
            submission=submission,
            documents=documents,
            form=form,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching submission: {e}")
        flash("Fehler beim Laden der Einreichung.", "error")
        return redirect(url_for("document.submissions"))


@bp.route("/submissions/<int:submission_id>/update-status", methods=["POST"])
def update_submission_status(submission_id: int) -> Any:
    """
    Update the status of a submission.

    Args:
        submission_id: Submission database ID

    Returns:
        Redirect to submission detail page
    """
    try:
        submission = db.session.query(Submission).filter_by(id=submission_id).first()

        if not submission:
            flash(f"Einreichung mit ID {submission_id} nicht gefunden.", "error")
            return redirect(url_for("document.submissions"))

        form = SubmissionStatusForm()

        if form.validate_on_submit():
            submission.status = form.status.data
            if form.notes.data:
                submission.notes = form.notes.data
            db.session.commit()

            flash("Status erfolgreich aktualisiert.", "success")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(error, "error")

        return redirect(url_for("document.submission_detail", submission_id=submission_id))

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while updating submission status: {e}")
        flash("Fehler beim Aktualisieren des Status.", "error")
        return redirect(url_for("document.submission_detail", submission_id=submission_id))


# Email import routes


@bp.route("/email-import", methods=["GET", "POST"])
def email_import() -> str | Any:
    """
    Import documents from email files.

    GET: Show import form
    POST: Process import and show results

    Returns:
        Rendered form template (GET) or results page (POST)
    """
    from app.forms.email import EmailImportForm
    from cli.email_cli import import_emails
    import tempfile

    try:
        courses = db.session.query(Course).order_by(Course.name).all()

        form = EmailImportForm()
        form.course_id.choices = [("", "-- Alle Kurse --")] + [
            (c.id, f"{c.name} ({c.semester})") for c in courses
        ]

        if form.validate_on_submit():
            file = form.file.data
            course_id = form.course_id.data if form.course_id.data else None

            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(
                suffix=Path(file.filename).suffix,
                delete=False,
            ) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name

            try:
                # Process the email file
                summary = import_emails(tmp_path, course_id)
                db.session.commit()

                return render_template(
                    "document/email_results.html",
                    summary=summary,
                )
            finally:
                # Clean up temp file
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except OSError:
                    pass

        # Show form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template(
            "document/email_import.html",
            form=form,
            courses=courses,
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error during email import: {e}")
        flash("Datenbankfehler beim E-Mail-Import.", "error")
        return redirect(url_for("document.index"))
