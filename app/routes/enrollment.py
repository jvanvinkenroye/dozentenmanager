"""
Enrollment routes blueprint.

This module provides web routes for managing student enrollments in courses.
"""

import logging
import os
from pathlib import Path
from typing import Any

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.datastructures import FileStorage

from app.forms.import_forms import EnrollmentImportForm
from app.models.course import Course
from app.models.enrollment import VALID_STATUSES
from app.models.student import Student
from app.services.enrollment_service import EnrollmentService
from app.services.student_service import StudentService
from app.utils.import_utils import (
    load_import_headers,
    load_import_rows,
    save_import_file,
)

ENROLLMENT_IMPORT_HEADERS = ["student_id"]

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("enrollment", __name__, url_prefix="/enrollments")


@bp.route("/courses/<int:course_id>/import-enrollments", methods=["GET", "POST"])
@login_required
def import_enrollments(course_id: int) -> str | Any:
    """Import enrollments (by Matrikelnummer) for a specific course."""
    from app import db

    course = db.session.get(Course, course_id)
    if not course:
        flash("Lehrveranstaltung nicht gefunden.", "error")
        return redirect(url_for("course.index"))

    form = EnrollmentImportForm()
    import_errors: list[str] = []
    import_summary: dict[str, int] | None = None
    mapping_headers: list[tuple[str, str]] = []
    mapping_token = ""
    mapping_format = ""
    mapping_defaults: dict[str, str] = {}

    if request.method == "POST" and request.form.get("mapping_token"):
        mapping_token = request.form.get("mapping_token", "").strip()
        mapping_format = request.form.get("file_format", "").strip()
        file_extension = request.form.get("file_extension", "data").strip()

        file_path = (
            Path(current_app.root_path)
            / "uploads"
            / "imports"
            / f"enrollments_{mapping_token}.{file_extension}"
        )
        mapping = {
            key: request.form.get(f"map_{key}", "").strip()
            for key in ENROLLMENT_IMPORT_HEADERS
        }
        mapping_defaults = mapping.copy()

        if not file_path.exists():
            flash("Importdatei nicht gefunden. Bitte erneut hochladen.", "error")
            return redirect(
                url_for("enrollment.import_enrollments", course_id=course_id)
            )

        try:
            with file_path.open("rb") as handle:
                f = FileStorage(stream=handle, filename=file_path.name)
                mapping_headers = load_import_headers(f, mapping_format)
                handle.seek(0)
                rows = load_import_rows(
                    f, mapping_format, ENROLLMENT_IMPORT_HEADERS, mapping=mapping
                )
        except ValueError as exc:
            import_errors.append(str(exc))
            return render_template(
                "enrollment/import.html",
                course=course,
                form=form,
                import_errors=import_errors,
                mapping_headers=mapping_headers,
                mapping_token=mapping_token,
                mapping_format=mapping_format,
                mapping_defaults=mapping_defaults,
                file_extension=file_extension,
            )

        enroll_service = EnrollmentService()
        student_service = StudentService()
        created = skipped = errors = 0

        for idx, row in enumerate(rows, start=2):
            matrikelnummer = row.get("student_id", "").strip()
            # Strip .0 suffix that Excel sometimes adds to numeric fields
            if matrikelnummer.endswith(".0"):
                matrikelnummer = matrikelnummer[:-2]
            if not matrikelnummer:
                import_errors.append(f"Zeile {idx}: Matrikelnummer fehlt.")
                errors += 1
                continue
            student = student_service.get_student_by_student_id(matrikelnummer)
            if not student:
                import_errors.append(
                    f"Zeile {idx}: Studierender '{matrikelnummer}' nicht gefunden."
                )
                errors += 1
                continue
            try:
                enroll_service.add_enrollment(
                    student_id_str=matrikelnummer, course_id=course_id
                )
                created += 1
            except IntegrityError:
                db.session.rollback()
                skipped += 1
            except ValueError as exc:
                import_errors.append(f"Zeile {idx}: {exc}")
                errors += 1

        if file_path.exists():
            try:
                os.remove(file_path)
            except OSError:
                logger.warning("Failed to remove import file %s", file_path)

        import_summary = {"created": created, "skipped": skipped, "errors": errors}
        return render_template(
            "enrollment/import.html",
            course=course,
            form=form,
            import_errors=import_errors,
            import_summary=import_summary,
        )

    if form.validate_on_submit():
        file = form.file.data
        try:
            token, file_path, extension = save_import_file(file, "enrollments")
            with file_path.open("rb") as handle:
                stored = FileStorage(stream=handle, filename=file_path.name)
                mapping_headers = load_import_headers(stored, form.file_format.data)
            mapping_token = token
            mapping_format = form.file_format.data
            normalized = [v for v, _ in mapping_headers]
            mapping_defaults = {
                k: k if k in normalized else "" for k in ENROLLMENT_IMPORT_HEADERS
            }
            return render_template(
                "enrollment/import.html",
                course=course,
                form=form,
                import_errors=import_errors,
                mapping_headers=mapping_headers,
                mapping_token=mapping_token,
                mapping_format=mapping_format,
                mapping_defaults=mapping_defaults,
                file_extension=extension,
            )
        except ValueError as exc:
            flash(str(exc), "error")

    for _field, errs in form.errors.items():
        for err in errs:
            flash(err, "error")

    return render_template(
        "enrollment/import.html",
        course=course,
        form=form,
        import_errors=import_errors,
    )


@bp.route("/enroll", methods=["POST"])
@login_required
def enroll() -> Any:
    """
    Enroll one or more students in a course.

    Form fields:
        student_ids: Student database IDs (required, can be multiple)
        course_id: Course database ID (required)
        redirect_to: Where to redirect after enrollment (optional)

    Returns:
        Redirect to course or student detail page
    """
    student_ids = [value.strip() for value in request.form.getlist("student_ids")]
    if not student_ids:
        single_id = request.form.get("student_id", "").strip()
        if single_id:
            student_ids = [single_id]
    course_id = request.form.get("course_id", "").strip()
    redirect_to = request.form.get("redirect_to", "").strip()

    # Validate inputs
    if not student_ids or not course_id:
        flash("Student and course are required.", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        course_id_int = int(course_id)
    except ValueError:
        flash("Invalid course ID.", "error")
        return redirect(request.referrer or url_for("index"))

    service = EnrollmentService()
    enrolled = 0
    already_enrolled = 0
    errors = 0
    first_student_db_id: int | None = None
    for student_db_id in student_ids:
        try:
            student_id_int = int(student_db_id)
        except ValueError:
            errors += 1
            continue

        try:
            student = (
                service.query(Student)
                .filter_by(id=student_id_int)
                .filter(Student.deleted_at.is_(None))
                .first()
            )
            if not student:
                errors += 1
                continue

            if first_student_db_id is None:
                first_student_db_id = student.id

            service.add_enrollment(student.student_id, course_id_int)
            enrolled += 1

        except IntegrityError:
            already_enrolled += 1
        except ValueError:
            errors += 1
        except SQLAlchemyError as e:
            logger.error(f"Database error while enrolling student: {e}")
            errors += 1

    if enrolled == 0 and errors == 0 and already_enrolled == 0:
        flash("Keine Studierenden ausgewählt.", "error")
        return redirect(request.referrer or url_for("index"))

    message = (
        f"Eingeschrieben: {enrolled}, "
        f"Bereits eingeschrieben: {already_enrolled}, "
        f"Fehler: {errors}"
    )
    flash(message, "success" if errors == 0 else "warning")

    if redirect_to == "student" and len(student_ids) == 1 and first_student_db_id:
        return redirect(url_for("student.show", student_id=first_student_db_id))
    return redirect(
        url_for("course.show", course_id=course_id_int)
        if course_id_int
        else (request.referrer or url_for("index"))
    )


@bp.route("/unenroll", methods=["POST"])
@login_required
def unenroll() -> Any:
    """
    Unenroll a student from a course.

    Form fields:
        student_id: Student database ID (required)
        course_id: Course database ID (required)
        redirect_to: Where to redirect after unenrollment (optional)

    Returns:
        Redirect to course or student detail page
    """
    student_db_id = request.form.get("student_id", "").strip()
    course_id = request.form.get("course_id", "").strip()
    redirect_to = request.form.get("redirect_to", "").strip()

    # Validate inputs
    if not student_db_id or not course_id:
        flash("Student and course are required.", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        student_id_int = int(student_db_id)
        course_id_int = int(course_id)
    except ValueError:
        flash("Invalid student or course ID.", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        # Get student to find their student_id (matriculation number)
        service = EnrollmentService()
        student = (
            service.query(Student)
            .filter_by(id=student_id_int)
            .filter(Student.deleted_at.is_(None))
            .first()
        )
        if not student:
            flash("Student not found.", "error")
            return redirect(request.referrer or url_for("index"))

        # Get enrollment for names before deleting
        enrollment = service.get_enrollment(student.student_id, course_id_int)
        if not enrollment:
            flash("Einschreibung nicht gefunden.", "error")
            return redirect(request.referrer or url_for("index"))

        student_name = f"{enrollment.student.first_name} {enrollment.student.last_name}"
        course_name = enrollment.course.name

        # Remove enrollment using service
        service.remove_enrollment(student.student_id, course_id_int)

        flash(
            f"{student_name} wurde erfolgreich aus '{course_name}' ausgetragen.",
            "success",
        )

        # Redirect based on redirect_to parameter
        if redirect_to == "student":
            return redirect(url_for("student.show", student_id=student.id))
        return redirect(url_for("course.show", course_id=course_id_int))

    except ValueError as e:
        flash(str(e), "error")
        return redirect(request.referrer or url_for("index"))

    except SQLAlchemyError as e:
        logger.error(f"Database error while unenrolling student: {e}")
        flash("Fehler beim Austragen. Bitte versuchen Sie es erneut.", "error")
        return redirect(request.referrer or url_for("index"))


@bp.route("/status", methods=["POST"])
@login_required
def update_status() -> Any:
    """
    Update enrollment status.

    Form fields:
        student_id: Student database ID (required)
        course_id: Course database ID (required)
        status: New status (active, completed, dropped) (required)
        redirect_to: Where to redirect after update (optional)

    Returns:
        Redirect to course or student detail page
    """
    student_db_id = request.form.get("student_id", "").strip()
    course_id = request.form.get("course_id", "").strip()
    status = request.form.get("status", "").strip()
    redirect_to = request.form.get("redirect_to", "").strip()

    # Validate inputs
    if not student_db_id or not course_id or not status:
        flash("Student, course, and status are required.", "error")
        return redirect(request.referrer or url_for("index"))

    if status not in VALID_STATUSES:
        flash(f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        student_id_int = int(student_db_id)
        course_id_int = int(course_id)
    except ValueError:
        flash("Invalid student or course ID.", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        # Get student to find their student_id (matriculation number)
        service = EnrollmentService()
        student = (
            service.query(Student)
            .filter_by(id=student_id_int)
            .filter(Student.deleted_at.is_(None))
            .first()
        )
        if not student:
            flash("Student not found.", "error")
            return redirect(request.referrer or url_for("index"))

        # Update enrollment status using service
        service.update_enrollment_status(student.student_id, course_id_int, status)

        flash(
            f"Status wurde auf '{status}' aktualisiert.",
            "success",
        )

        # Redirect based on redirect_to parameter
        if redirect_to == "student":
            return redirect(url_for("student.show", student_id=student.id))
        return redirect(url_for("course.show", course_id=course_id_int))

    except ValueError as e:
        flash(str(e), "error")
        return redirect(request.referrer or url_for("index"))

    except SQLAlchemyError as e:
        logger.error(f"Database error while updating enrollment status: {e}")
        flash(
            "Fehler beim Aktualisieren des Status. Bitte versuchen Sie es erneut.",
            "error",
        )
        return redirect(request.referrer or url_for("index"))
