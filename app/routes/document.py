"""
Document routes blueprint.

This module provides web routes for managing documents through the Flask interface.
"""

import contextlib
import logging
import mimetypes
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from flask_login import login_required
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
)
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.student import Student
from app.models.submission import Submission
from app.services.document_service import DocumentService
from app.utils.auth import admin_required, lecturer_required

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("document", __name__, url_prefix="/documents")


@bp.route("/")
@login_required
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
    service = DocumentService()

    try:
        # Get filter parameters
        course_id = request.args.get("course_id", type=int)
        student_id = request.args.get("student_id", type=int)
        file_type = request.args.get("file_type", "").strip()
        status = request.args.get("status", "").strip()

        # Get documents using service
        documents = service.list_documents(
            course_id=course_id,
            student_id=student_id,
            file_type=file_type,
            status=status,
        )

        # Get filter options (still need direct queries for dropdowns efficiently)
        courses = db.session.query(Course).order_by(Course.name).all()
        students = (
            db.session.query(Student)
            .filter(Student.deleted_at.is_(None))
            .order_by(Student.last_name)
            .all()
        )

        # Populate form choices
        form.course_id.choices = [("", "-- Alle Kurse --")] + [
            (str(c.id), str(c.name)) for c in courses
        ]  # type: ignore
        form.student_id.choices = [("", "-- Alle Studierende --")] + [
            (str(s.id), f"{s.last_name}, {s.first_name} ({s.student_id})") for s in students
        ]  # type: ignore

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
@login_required
def show(document_id: int) -> str | Any:
    """
    Show details for a specific document.

    Args:
        document_id: Document database ID

    Returns:
        Rendered template with document details or redirect
    """
    service = DocumentService()
    try:
        document = service.get_document(document_id)
        form = SubmissionStatusForm(obj=document.submission)
        return render_template(
            "document/detail.html",
            document=document,
            form=form,
        )

    except ValueError:
        flash(f"Dokument mit ID {document_id} nicht gefunden.", "error")
        return redirect(url_for("document.index"))

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching document: {e}")
        flash("Fehler beim Laden des Dokuments.", "error")
        return redirect(url_for("document.index"))


@bp.route("/<int:document_id>/download")
@login_required
def download(document_id: int) -> Any:
    """
    Download a document.

    Args:
        document_id: Document database ID

    Returns:
        File download response or redirect on error
    """
    service = DocumentService()
    try:
        document = service.get_document(document_id)
        
        file_path = Path(document.file_path)
        if not file_path.exists():
            flash("Datei nicht gefunden auf dem Server.", "error")
            return redirect(url_for("document.show", document_id=document_id))

        return send_file(  # type: ignore[call-arg]
            file_path,
            as_attachment=True,
            download_name=document.original_filename,
            mimetype=document.mime_type,
        )

    except ValueError:
        flash(f"Dokument mit ID {document_id} nicht gefunden.", "error")
        return redirect(url_for("document.index"))

    except Exception as e:
        logger.error(f"Error while downloading document: {e}")
        flash("Fehler beim Herunterladen der Datei.", "error")
        return redirect(url_for("document.index"))


@bp.route("/upload", methods=["GET", "POST"])
@lecturer_required
def upload() -> str | Any:
    """
    Upload a new document.

    GET: Show upload form
    POST: Process upload and redirect to document detail

    Returns:
        Rendered form template (GET) or redirect (POST)
    """
    service = DocumentService()
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
            (str(ex.id), f"{ex.name} ({ex.course.name})") for ex in exams
        ]  # type: ignore

        if form.validate_on_submit():
            file = form.file.data
            original_filename = secure_filename(file.filename)
            
            # Save uploaded file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name

            try:
                document = service.upload_document(
                    file_path=tmp_path,
                    enrollment_id=form.enrollment_id.data,
                    submission_type=form.submission_type.data,
                    exam_id=form.exam_id.data if form.exam_id.data else None,
                    notes=form.notes.data if form.notes.data else None,
                    original_filename=original_filename,
                )

                flash(f"Dokument '{document.original_filename}' erfolgreich hochgeladen.", "success")
                return redirect(url_for("document.show", document_id=document.id))
            
            except ValueError as e:
                flash(str(e), "error")
            finally:
                # Clean up temp file
                with contextlib.suppress(OSError):
                    Path(tmp_path).unlink(missing_ok=True)

        # Show form validation errors
        for _field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("document/upload.html", form=form)

    except SQLAlchemyError as e:
        logger.error(f"Database error while uploading document: {e}")
        flash("Datenbankfehler beim Hochladen.", "error")
        return redirect(url_for("document.index"))


@bp.route("/bulk-upload", methods=["GET", "POST"])
@login_required
@admin_required
def bulk_upload() -> str | Any:
    """
    Upload multiple documents at once.

    GET: Show bulk upload form
    POST: Process uploads and show results

    Returns:
        Rendered form template (GET) or results page (POST)
    """
    service = DocumentService()
    try:
        courses = db.session.query(Course).order_by(Course.name).all()
        exams = db.session.query(Exam).order_by(Exam.exam_date.desc()).all()

        form = BulkDocumentUploadForm()
        form.course_id.choices = [(int(c.id), str(c.name)) for c in courses]
        form.exam_id.choices = [("", "-- Keine Prüfung --")] + [
            (str(ex.id), f"{ex.name} ({ex.course.name})") for ex in exams
        ]  # type: ignore

        if form.validate_on_submit():
            files = request.files.getlist("files")
            course_id = form.course_id.data
            submission_type = form.submission_type.data
            exam_id = form.exam_id.data if form.exam_id.data else None
            notes = form.notes.data

            results: dict[str, list] = {"success": [], "failed": [], "unmatched": []}

            import tempfile

            for file in files:
                if not file or not file.filename:
                    continue

                original_filename = secure_filename(file.filename)

                if not allowed_file(original_filename):
                    results["failed"].append(
                        {
                            "filename": original_filename,
                            "reason": "Dateityp nicht erlaubt",
                        }
                    )
                    continue

                # Try to match file to student using service
                matched_enrollment = service.match_file_to_enrollment(
                    original_filename, course_id
                )

                if not matched_enrollment:
                    results["unmatched"].append(original_filename)
                    continue

                # Save temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(original_filename).suffix) as tmp:
                    file.save(tmp.name)
                    tmp_path = tmp.name

                try:
                    service.upload_document(
                        file_path=tmp_path,
                        enrollment_id=matched_enrollment.id,
                        submission_type=submission_type,
                        exam_id=exam_id,
                        notes=notes,
                        original_filename=original_filename,
                    )

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
                finally:
                    # Clean up temp file
                    with contextlib.suppress(OSError):
                        Path(tmp_path).unlink(missing_ok=True)

            return render_template(
                "document/bulk_results.html",
                results=results,
                total=len(files),
            )

        # Show form validation errors
        for _field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("document/bulk_upload.html", form=form, courses=courses)

    except SQLAlchemyError as e:
        logger.error(f"Database error during bulk upload: {e}")
        flash("Datenbankfehler beim Hochladen.", "error")
        return redirect(url_for("document.index"))


@bp.route("/<int:document_id>/delete", methods=["GET", "POST"])
@login_required
@admin_required
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
    service = DocumentService()
    try:
        try:
            document = service.get_document(document_id)
        except ValueError:
            flash(f"Dokument mit ID {document_id} nicht gefunden.", "error")
            return redirect(url_for("document.index"))

        if request.method == "GET":
            return render_template("document/delete.html", document=document)

        # POST: Delete document
        document_name = document.original_filename
        service.delete_document(document_id)

        flash(f"Dokument '{document_name}' erfolgreich gelöscht.", "success")
        return redirect(url_for("document.index"))

    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting document: {e}")
        flash("Fehler beim Löschen des Dokuments.", "error")
        return redirect(url_for("document.show", document_id=document_id))


# Submission routes


@bp.route("/submissions")
@login_required
def submissions() -> str:
    """
    List all submissions.

    Query parameters:
        course_id: Optional course filter
        status: Optional status filter

    Returns:
        Rendered template with list of submissions
    """
    service = DocumentService()
    try:
        # Get filter parameters
        course_id = request.args.get("course_id", type=int)
        status = request.args.get("status", "").strip()

        # Get submissions using service
        submissions_list = service.list_submissions(
            course_id=course_id,
            status=status,
        )

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
@login_required
def submission_detail(submission_id: int) -> str | Any:
    """
    Show details for a specific submission.

    Args:
        submission_id: Submission database ID

    Returns:
        Rendered template with submission details or redirect
    """
    service = DocumentService()
    try:
        submission = service.get_submission(submission_id)
        documents = submission.documents.all()
        form = SubmissionStatusForm(obj=submission)

        return render_template(
            "document/submission_detail.html",
            submission=submission,
            documents=documents,
            form=form,
        )

    except ValueError:
        flash(f"Einreichung mit ID {submission_id} nicht gefunden.", "error")
        return redirect(url_for("document.submissions"))

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching submission: {e}")
        flash("Fehler beim Laden der Einreichung.", "error")
        return redirect(url_for("document.submissions"))


@bp.route("/submissions/<int:submission_id>/update-status", methods=["POST"])
@lecturer_required
def update_submission_status(submission_id: int) -> Any:
    """
    Update the status of a submission.

    Args:
        submission_id: Submission database ID

    Returns:
        Redirect to submission detail page
    """
    service = DocumentService()
    try:
        # We need to fetch it first to handle "not found" gracefully for redirect
        try:
            service.get_submission(submission_id)
        except ValueError:
             flash(f"Einreichung mit ID {submission_id} nicht gefunden.", "error")
             return redirect(url_for("document.submissions"))

        form = SubmissionStatusForm()

        if form.validate_on_submit():
            service.update_submission_status(
                submission_id=submission_id,
                status=form.status.data,
                notes=form.notes.data or None
            )
            flash("Status erfolgreich aktualisiert.", "success")
        else:
            for _field, errors in form.errors.items():
                for error in errors:
                    flash(error, "error")

        return redirect(
            url_for("document.submission_detail", submission_id=submission_id)
        )

    except ValueError as e:
        flash(str(e), "error")
        return redirect(
            url_for("document.submission_detail", submission_id=submission_id)
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while updating submission status: {e}")
        flash("Fehler beim Aktualisieren des Status.", "error")
        return redirect(
            url_for("document.submission_detail", submission_id=submission_id)
        )


# Email import routes


@bp.route("/email-import", methods=["GET", "POST"])
@login_required
@admin_required
def email_import() -> str | Any:
    """
    Import documents from email files.

    GET: Show import form
    POST: Process import and show results

    Returns:
        Rendered form template (GET) or results page (POST)
    """
    import tempfile

    from app.forms.email import EmailImportForm
    from cli.email_cli import import_emails

    try:
        courses = db.session.query(Course).order_by(Course.name).all()

        form = EmailImportForm()
        form.course_id.choices = [("", "-- Alle Kurse --")] + [
            (str(c.id), f"{c.name} ({c.semester})") for c in courses
        ]  # type: ignore

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
                with contextlib.suppress(OSError):
                    Path(tmp_path).unlink(missing_ok=True)

        # Show form validation errors
        for _field, errors in form.errors.items():
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
