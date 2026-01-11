"""
Student routes blueprint.

This module provides web routes for managing students through the Flask interface.
"""

import csv
import io
import logging
from typing import Any

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import FileStorage

from app import db
from app.forms.student import StudentForm, StudentImportForm
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.student import Student, validate_email
from app.models.submission import Submission
from app.services.student_service import StudentService
from app.utils.pagination import paginate_query

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("student", __name__, url_prefix="/students")

REQUIRED_IMPORT_HEADERS = [
    "first_name",
    "last_name",
    "student_id",
    "email",
    "program",
]


def _normalize_header(header: str | None) -> str:
    if not header:
        return ""
    return header.strip().lower()


def _load_csv_rows(file: FileStorage) -> list[dict[str, str]]:
    file.stream.seek(0)
    text_stream = io.TextIOWrapper(file.stream, encoding="utf-8-sig")
    reader = csv.DictReader(text_stream)
    raw_headers = reader.fieldnames or []
    normalized_headers = [_normalize_header(h) for h in raw_headers]
    header_map = dict(zip(raw_headers, normalized_headers, strict=False))
    missing = [h for h in REQUIRED_IMPORT_HEADERS if h not in normalized_headers]
    if missing:
        raise ValueError("Missing required headers: " + ", ".join(missing))

    rows: list[dict[str, str]] = []
    for row in reader:
        normalized_row: dict[str, str] = {}
        for raw_header, value in row.items():
            normalized_key = header_map.get(raw_header, "")
            if not normalized_key:
                continue
            normalized_row[normalized_key] = str(value).strip() if value else ""
        rows.append(normalized_row)
    return rows


def _load_xlsx_rows(file: FileStorage) -> list[dict[str, str]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ValueError(
            "openpyxl is required for XLSX import. Install it and try again."
        ) from exc

    file.stream.seek(0)
    workbook = load_workbook(
        filename=io.BytesIO(file.stream.read()),
        read_only=True,
        data_only=True,
    )
    sheet = workbook.active
    rows_iter = sheet.iter_rows(values_only=True)
    try:
        headers = next(rows_iter)
    except StopIteration:
        raise ValueError("XLSX file has no rows.") from None

    raw_headers = [_normalize_header(str(h)) for h in headers]
    missing = [h for h in REQUIRED_IMPORT_HEADERS if h not in raw_headers]
    if missing:
        raise ValueError("Missing required headers: " + ", ".join(missing))

    rows: list[dict[str, str]] = []
    for row in rows_iter:
        normalized_row: dict[str, str] = {}
        for idx, value in enumerate(row):
            header = raw_headers[idx] if idx < len(raw_headers) else ""
            if not header:
                continue
            normalized_row[header] = str(value).strip() if value is not None else ""
        rows.append(normalized_row)
    return rows


def _load_xls_rows(file: FileStorage) -> list[dict[str, str]]:
    try:
        import xlrd
    except ImportError as exc:
        raise ValueError(
            "xlrd is required for XLS import. Install it and try again."
        ) from exc

    file.stream.seek(0)
    workbook = xlrd.open_workbook(file_contents=file.stream.read())
    if workbook.nsheets == 0:
        raise ValueError("XLS file has no sheets.")

    sheet = workbook.sheet_by_index(0)
    if sheet.nrows == 0:
        raise ValueError("XLS file has no rows.")

    raw_headers = [_normalize_header(str(h)) for h in sheet.row_values(0)]
    missing = [h for h in REQUIRED_IMPORT_HEADERS if h not in raw_headers]
    if missing:
        raise ValueError("Missing required headers: " + ", ".join(missing))

    rows: list[dict[str, str]] = []
    for row_idx in range(1, sheet.nrows):
        row = sheet.row_values(row_idx)
        normalized_row: dict[str, str] = {}
        for idx, value in enumerate(row):
            header = raw_headers[idx] if idx < len(raw_headers) else ""
            if not header:
                continue
            normalized_row[header] = str(value).strip() if value else ""
        rows.append(normalized_row)
    return rows


def _load_import_rows(file: FileStorage, fmt: str | None) -> list[dict[str, str]]:
    format_hint = fmt or file.filename.rsplit(".", 1)[-1].lower()
    if format_hint == "csv":
        return _load_csv_rows(file)
    if format_hint == "xlsx":
        return _load_xlsx_rows(file)
    if format_hint == "xls":
        return _load_xls_rows(file)
    raise ValueError(f"Unsupported format '{format_hint}'. Use csv, xlsx, or xls.")


@bp.route("/")
def index() -> str:
    """
    List all students with optional search, program filter, and pagination.

    Query parameters:
        search: Optional search term to filter by name, student_id, or email
        program: Optional program filter
        page: Page number (default: 1)

    Returns:
        Rendered template with paginated list of students
    """
    search_term = request.args.get("search", "").strip()
    program_filter = request.args.get("program", "").strip()
    service = StudentService()

    try:
        # Build query using service's query method
        query = service.query(Student).filter(Student.deleted_at.is_(None))

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                (Student.first_name.ilike(search_pattern))
                | (Student.last_name.ilike(search_pattern))
                | (Student.student_id.ilike(search_pattern))
                | (Student.email.ilike(search_pattern))
            )

        if program_filter:
            program_pattern = f"%{program_filter}%"
            query = query.filter(Student.program.ilike(program_pattern))

        query = query.order_by(Student.last_name, Student.first_name)
        pagination = paginate_query(query, per_page=20)

        return render_template(
            "student/list.html",
            students=pagination.items,
            pagination=pagination,
            search_term=search_term,
            program_filter=program_filter,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing students: {e}")
        flash("Error loading students. Please try again.", "error")
        return render_template(
            "student/list.html",
            students=[],
            pagination=None,
            search_term="",
            program_filter="",
        )


@bp.route("/<int:student_id>")
def show(student_id: int) -> str | Any:
    """
    Show details for a specific student.

    Args:
        student_id: Student database ID

    Returns:
        Rendered template with student details or redirect
    """
    service = StudentService()

    try:
        student = service.get_student(student_id)

        if not student:
            flash(f"Student mit Datenbank-ID {student_id} nicht gefunden.", "error")
            return redirect(url_for("student.index"))

        enrollments = (
            db.session.query(Enrollment)
            .join(Course)
            .filter(Enrollment.student_id == student.id)
            .order_by(Course.semester.desc(), Course.name)
            .all()
        )
        grades_count = (
            db.session.query(Grade)
            .join(Enrollment)
            .filter(Enrollment.student_id == student.id)
            .count()
        )
        submissions = (
            db.session.query(Submission)
            .join(Enrollment)
            .filter(Enrollment.student_id == student.id)
            .order_by(Submission.submission_date.desc())
            .limit(5)
            .all()
        )

        return render_template(
            "student/detail.html",
            student=student,
            enrollments=enrollments,
            grades_count=grades_count,
            submissions=submissions,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching student: {e}")
        flash("Error loading student details. Please try again.", "error")
        return redirect(url_for("student.index"))


@bp.route("/new", methods=["GET", "POST"])
def new() -> str | Any:
    """
    Create a new student.

    GET: Show form
    POST: Create student and redirect to detail page

    Form fields:
        first_name: First name (required)
        last_name: Last name (required)
        student_id: Student ID (required, 8 digits)
        email: Email address (required)
        program: Study program (required)

    Returns:
        Rendered form template (GET) or redirect to detail page (POST)
    """
    form = StudentForm()
    service = StudentService()

    if form.validate_on_submit():
        try:
            # Create new student using service
            student = service.add_student(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                student_id=form.student_id.data,
                email=form.email.data,
                program=form.program.data,
            )

            logger.info(
                f"Created student: {student.first_name} {student.last_name} ({student.student_id})"
            )
            flash(
                f"Student '{student.first_name} {student.last_name}' created successfully.",
                "success",
            )
            return redirect(url_for("student.show", student_id=student.id))

        except ValueError as e:
            logger.error(f"Validation error while creating student: {e}")
            flash(str(e), "error")

        except SQLAlchemyError as e:
            logger.error(f"Database error while creating student: {e}")
            flash("Error creating student. Please try again.", "error")

    # Display form validation errors
    for _field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("student/form.html", student=None, form=form)


@bp.route("/export")
def export_students() -> Response:
    """Export students to CSV with optional filters."""
    search_term = request.args.get("search", "").strip()
    program_filter = request.args.get("program", "").strip()
    service = StudentService()

    try:
        query = service.query(Student).filter(Student.deleted_at.is_(None))

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                (Student.first_name.ilike(search_pattern))
                | (Student.last_name.ilike(search_pattern))
                | (Student.student_id.ilike(search_pattern))
                | (Student.email.ilike(search_pattern))
            )

        if program_filter:
            program_pattern = f"%{program_filter}%"
            query = query.filter(Student.program.ilike(program_pattern))

        students = query.order_by(Student.last_name, Student.first_name).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while exporting students: {e}")
        flash("Fehler beim Export der Studierenden.", "error")
        return redirect(url_for("student.index"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["first_name", "last_name", "student_id", "email", "program"])
    for student in students:
        writer.writerow(
            [
                student.first_name,
                student.last_name,
                student.student_id,
                student.email,
                student.program,
            ]
        )

    filename = "students_export.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@bp.route("/import", methods=["GET", "POST"])
def import_students() -> str | Any:
    """Import students from CSV/XLSX/XLS."""
    form = StudentImportForm()
    service = StudentService()
    import_errors: list[str] = []

    if form.validate_on_submit():
        file = form.file.data
        try:
            rows = _load_import_rows(file, form.file_format.data)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template(
                "student/import.html",
                form=form,
                import_errors=import_errors,
            )

        created = updated = skipped = errors = 0
        seen_student_ids: set[str] = set()
        seen_emails: set[str] = set()

        for idx, row in enumerate(rows, start=2):
            missing_values = [
                header for header in REQUIRED_IMPORT_HEADERS if not row.get(header)
            ]
            if missing_values:
                errors += 1
                import_errors.append(
                    f"Zeile {idx}: fehlende Werte: {', '.join(missing_values)}"
                )
                continue

            student_id = row["student_id"].strip()
            email = row["email"].strip().lower()

            if not student_id:
                errors += 1
                import_errors.append(f"Zeile {idx}: fehlende Matrikelnummer")
                continue
            if not validate_email(email):
                errors += 1
                import_errors.append(f"Zeile {idx}: ungültige E-Mail {email}")
                continue

            if student_id in seen_student_ids or email in seen_emails:
                errors += 1
                import_errors.append(f"Zeile {idx}: Duplikat innerhalb der Datei")
                continue
            seen_student_ids.add(student_id)
            seen_emails.add(email)

            existing_by_id = (
                db.session.query(Student).filter_by(student_id=student_id).first()
            )
            existing_by_email = db.session.query(Student).filter_by(email=email).first()

            existing: Student | None = None
            if existing_by_id and existing_by_email:
                if existing_by_id.id != existing_by_email.id:
                    errors += 1
                    import_errors.append(
                        f"Zeile {idx}: Matrikelnummer und E-Mail gehören zu unterschiedlichen Datensätzen"
                    )
                    continue
                existing = existing_by_id
            else:
                existing = existing_by_id or existing_by_email

            if existing:
                if form.on_duplicate.data == "skip":
                    skipped += 1
                    continue
                if form.on_duplicate.data == "error":
                    errors += 1
                    import_errors.append(f"Zeile {idx}: Duplikat gefunden")
                    continue
                if form.on_duplicate.data == "update":
                    if existing.deleted_at:
                        existing.deleted_at = None
                    try:
                        existing_id = int(existing.id)
                        updated_student = service.update_student(
                            existing_id,
                            row["first_name"],
                            row["last_name"],
                            student_id,
                            email,
                            row["program"],
                            validate_id=False,
                        )
                        if updated_student:
                            updated += 1
                        else:
                            errors += 1
                            import_errors.append(
                                f"Zeile {idx}: Datensatz nicht gefunden"
                            )
                    except ValueError as exc:
                        errors += 1
                        import_errors.append(f"Zeile {idx}: {exc}")
                    except SQLAlchemyError:
                        errors += 1
                        import_errors.append(f"Zeile {idx}: Datenbankfehler")
                    continue

            try:
                service.add_student(
                    row["first_name"],
                    row["last_name"],
                    student_id,
                    email,
                    row["program"],
                    validate_id=False,
                )
                created += 1
            except ValueError as exc:
                errors += 1
                import_errors.append(f"Zeile {idx}: {exc}")
            except SQLAlchemyError:
                errors += 1
                import_errors.append(f"Zeile {idx}: Datenbankfehler")

        flash(
            f"Import abgeschlossen. Neu: {created}, "
            f"Aktualisiert: {updated}, Übersprungen: {skipped}, "
            f"Fehler: {errors}",
            "success" if errors == 0 else "warning",
        )

    return render_template(
        "student/import.html",
        form=form,
        import_errors=import_errors,
    )


@bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
def edit(student_id: int) -> str | Any:
    """
    Edit an existing student.

    GET: Show edit form
    POST: Update student and redirect to detail page

    Args:
        student_id: Student database ID

    Form fields:
        first_name: First name (required)
        last_name: Last name (required)
        student_id: Student ID (required)
        email: Email address (required)
        program: Study program (required)

    Returns:
        Rendered form template (GET) or redirect to detail page (POST)
    """
    service = StudentService()

    try:
        student = service.get_student(student_id)

        if not student:
            flash(f"Student mit Datenbank-ID {student_id} nicht gefunden.", "error")
            return redirect(url_for("student.index"))

        form = StudentForm(student=student, obj=student)

        if form.validate_on_submit():
            try:
                # Update using service
                student = service.update_student(
                    student_id=student_id,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    student_number=form.student_id.data,
                    email=form.email.data,
                    program=form.program.data,
                )

                if student:
                    logger.info(
                        f"Updated student: {student.first_name} {student.last_name} ({student.student_id})"
                    )
                    flash(
                        f"Student '{student.first_name} {student.last_name}' updated successfully.",
                        "success",
                    )
                    return redirect(url_for("student.show", student_id=student.id))

            except ValueError as e:
                logger.error(f"Validation error while updating student: {e}")
                flash(str(e), "error")

            except SQLAlchemyError as e:
                logger.error(f"Database error while updating student: {e}")
                flash("Error updating student. Please try again.", "error")

        # Display form validation errors
        for _field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("student/form.html", student=student, form=form)

    except SQLAlchemyError as e:
        logger.error(f"Database error while loading student: {e}")
        flash("Error loading student. Please try again.", "error")
        return redirect(url_for("student.index"))


@bp.route("/<int:student_id>/delete", methods=["GET", "POST"])
def delete(student_id: int) -> str | Any:
    """
    Delete a student.

    GET: Show confirmation page
    POST: Delete student and redirect to list

    Args:
        student_id: Student database ID

    Returns:
        Rendered confirmation template (GET) or redirect to list (POST)
    """
    service = StudentService()

    try:
        student = service.get_student(student_id)

        if not student:
            flash(f"Student mit Datenbank-ID {student_id} nicht gefunden.", "error")
            return redirect(url_for("student.index"))

        if request.method == "GET":
            return render_template("student/delete.html", student=student)

        # POST: Delete student using service
        student_name = f"{student.first_name} {student.last_name}"
        if service.delete_student(student_id):
            flash(f"Student '{student_name}' deleted successfully.", "success")
            return redirect(url_for("student.index"))

        flash(f"Error deleting student '{student_name}'.", "error")
        return redirect(url_for("student.show", student_id=student_id))

    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting student: {e}")
        flash("Error deleting student. Please try again.", "error")
        return redirect(url_for("student.show", student_id=student_id))
