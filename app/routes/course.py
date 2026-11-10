"""
Course routes blueprint.

This module provides web routes for managing courses through the Flask interface.
"""

import logging
import os
from pathlib import Path
from typing import Any, cast

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

from app import db
from app.forms.course import CourseForm
from app.forms.import_forms import CourseImportForm
from app.models.course import Course
from app.models.student import Student
from app.models.university import University
from app.services.course_service import CourseService
from app.utils.auth import admin_required, lecturer_required
from app.utils.import_utils import (
    load_import_headers,
    load_import_rows,
    save_import_file,
)
from app.utils.pagination import paginate_query

COURSE_IMPORT_HEADERS = ["name", "semester"]

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("course", __name__, url_prefix="/courses")


@bp.route("/")
@login_required
def index() -> str:
    """
    List all courses with optional search, filters, and pagination.

    Query parameters:
        search: Optional search term to filter by name
        university_id: Optional university filter
        semester: Optional semester filter
        page: Page number (default: 1)

    Returns:
        Rendered template with paginated list of courses
    """
    search_term = request.args.get("search", "").strip()
    university_id = request.args.get("university_id", "").strip()
    semester_filter = request.args.get("semester", "").strip()
    service = CourseService()

    try:
        # Build query using service's query method
        query = service.query(Course)

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(Course.name.ilike(search_pattern))

        if university_id:
            query = query.filter_by(university_id=int(university_id))

        if semester_filter:
            query = query.filter_by(semester=semester_filter)

        query = query.order_by(Course.semester.desc(), Course.name)
        pagination = paginate_query(query, per_page=20)

        # Get all universities for filter dropdown
        universities = db.session.query(University).order_by(University.name).all()

        return render_template(
            "course/list.html",
            courses=pagination.items,
            pagination=pagination,
            universities=universities,
            search_term=search_term,
            university_id=university_id,
            semester_filter=semester_filter,
        )

    except (SQLAlchemyError, ValueError) as e:
        logger.error(f"Error while listing courses: {e}")
        flash("Error loading courses. Please try again.", "error")
        return render_template(
            "course/list.html",
            courses=[],
            pagination=None,
            universities=[],
            search_term="",
            university_id="",
            semester_filter="",
        )


@bp.route("/<int:course_id>")
@login_required
def show(course_id: int) -> str | Any:
    """
    Show details for a specific course.

    Args:
        course_id: Course database ID

    Returns:
        Rendered template with course details or redirect
    """
    service = CourseService()

    try:
        from app.models.enrollment import Enrollment
        from app.models.exam import Exam
        from app.models.submission import Submission

        course = service.get_course(course_id)

        if not course:
            flash(f"Course with ID {course_id} not found.", "error")
            return redirect(url_for("course.index"))

        # Get enrollments for this course
        enrollments = (
            db.session.query(Enrollment)
            .join(Student)
            .filter(Enrollment.course_id == course_id)
            .filter(Student.deleted_at.is_(None))
            .all()
        )

        # Get all students for enrollment dropdown (students not already enrolled)
        enrolled_student_ids = [e.student_id for e in enrollments]
        available_students = (
            db.session.query(Student)
            .filter(Student.deleted_at.is_(None))
            .filter(
                ~Student.id.in_(enrolled_student_ids) if enrolled_student_ids else True  # type: ignore[arg-type]
            )
            .order_by(Student.last_name, Student.first_name)
            .all()
        )

        exams = (
            db.session.query(Exam)
            .filter_by(course_id=course_id)
            .order_by(Exam.exam_date.desc(), Exam.name)
            .all()
        )

        submissions_count = (
            db.session.query(Submission)
            .join(Enrollment)
            .filter(Enrollment.course_id == course_id)
            .count()
        )

        return render_template(
            "course/detail.html",
            course=course,
            enrollments=enrollments,
            available_students=available_students,
            exams=exams,
            submissions_count=submissions_count,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching course: {e}")
        flash("Error loading course details. Please try again.", "error")
        return redirect(url_for("course.index"))


@bp.route("/new", methods=["GET", "POST"])
@lecturer_required
def new() -> str | Any:
    """
    Create a new course.

    GET: Show form
    POST: Create course and redirect to detail page

    Form fields:
        name: Course name (required)
        semester: Semester (required, format: YYYY_SoSe or YYYY_WiSe)
        university_id: University ID (required)
        slug: Custom slug (optional, auto-generated if not provided)

    Returns:
        Rendered form template (GET) or redirect to detail page (POST)
    """
    service = CourseService()

    # Get universities for dropdown
    try:
        universities = db.session.query(University).order_by(University.name).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while loading universities: {e}")
        flash("Error loading universities. Please try again.", "error")
        return redirect(url_for("course.index"))

    form = CourseForm()
    form.university_id.choices = [(int(u.id), str(u.name)) for u in universities]

    if form.validate_on_submit():
        try:
            # Create new course using service
            course = service.add_course(
                name=cast(str, form.name.data),
                semester=cast(str, form.semester.data),
                university_id=form.university_id.data,
                slug=form.slug.data,
            )

            logger.info(f"Created course: {course.name} ({course.semester})")
            flash(f"Course '{course.name}' created successfully.", "success")
            return redirect(url_for("course.show", course_id=course.id))

        except ValueError as e:
            logger.error(f"Validation error while creating course: {e}")
            flash(str(e), "error")

        except SQLAlchemyError as e:
            logger.error(f"Database error while creating course: {e}")
            flash("Error creating course. Please try again.", "error")

    # Display form validation errors
    for _field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template(
        "course/form.html", course=None, form=form, universities=universities
    )


@bp.route("/<int:course_id>/edit", methods=["GET", "POST"])
@lecturer_required
def edit(course_id: int) -> str | Any:
    """
    Edit an existing course.

    GET: Show edit form
    POST: Update course and redirect to detail page

    Args:
        course_id: Course database ID

    Form fields:
        name: Course name (required)
        semester: Semester (required)
        university_id: University ID (required)
        slug: Custom slug (optional)

    Returns:
        Rendered form template (GET) or redirect to detail page (POST)
    """
    service = CourseService()

    try:
        course = service.get_course(course_id)

        if not course:
            flash(f"Course with ID {course_id} not found.", "error")
            return redirect(url_for("course.index"))

        # Get universities for dropdown
        universities = db.session.query(University).order_by(University.name).all()

        form = CourseForm(course=course, obj=course)
        form.university_id.choices = [(int(u.id), str(u.name)) for u in universities]

        if form.validate_on_submit():
            try:
                # Update using service
                course = service.update_course(
                    course_id=course_id,
                    name=form.name.data,
                    semester=form.semester.data,
                    university_id=form.university_id.data,
                    slug=form.slug.data,
                )

                if course:
                    logger.info(f"Updated course: {course.name} ({course.semester})")
                    flash(f"Course '{course.name}' updated successfully.", "success")
                    return redirect(url_for("course.show", course_id=course.id))

            except ValueError as e:
                logger.error(f"Validation error while updating course: {e}")
                flash(str(e), "error")

            except SQLAlchemyError as e:
                logger.error(f"Database error while updating course: {e}")
                flash("Error updating course. Please try again.", "error")

        # Display form validation errors
        for _field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template(
            "course/form.html", course=course, form=form, universities=universities
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while loading course: {e}")
        flash("Error loading course. Please try again.", "error")
        return redirect(url_for("course.index"))


@bp.route("/import", methods=["GET", "POST"])
@login_required
@lecturer_required
def import_courses() -> str | Any:
    """Import courses from CSV/XLSX/XLS."""
    service = CourseService()
    universities = db.session.query(University).order_by(University.name).all()

    form = CourseImportForm()
    form.university_id.choices = [(int(u.id), str(u.name)) for u in universities]

    import_errors: list[str] = []
    import_summary: dict[str, int] | None = None
    mapping_headers: list[tuple[str, str]] = []
    mapping_token = ""
    mapping_format = ""
    mapping_defaults: dict[str, str] = {}
    mapping_university_id = ""
    mapping_on_duplicate = "skip"

    if request.method == "POST" and request.form.get("mapping_token"):
        mapping_token = request.form.get("mapping_token", "").strip()
        mapping_format = request.form.get("file_format", "").strip()
        mapping_on_duplicate = request.form.get("on_duplicate", "skip").strip()
        file_extension = request.form.get("file_extension", "data").strip()
        mapping_university_id = request.form.get("university_id", "").strip()

        try:
            university_id = int(mapping_university_id)
        except (ValueError, TypeError):
            flash("Bitte eine Hochschule auswählen.", "error")
            return render_template(
                "course/import.html",
                form=form,
                universities=universities,
                import_errors=import_errors,
            )

        file_path = (
            Path(current_app.root_path)
            / "uploads"
            / "imports"
            / f"courses_{mapping_token}.{file_extension}"
        )
        mapping = {
            key: request.form.get(f"map_{key}", "").strip()
            for key in COURSE_IMPORT_HEADERS
        }
        mapping_defaults = mapping.copy()

        if not file_path.exists():
            flash("Importdatei nicht gefunden. Bitte erneut hochladen.", "error")
            return redirect(url_for("course.import_courses"))

        try:
            with file_path.open("rb") as handle:
                f = FileStorage(stream=handle, filename=file_path.name)
                mapping_headers = load_import_headers(f, mapping_format)
                handle.seek(0)
                rows = load_import_rows(
                    f, mapping_format, COURSE_IMPORT_HEADERS, mapping=mapping
                )
        except ValueError as exc:
            import_errors.append(str(exc))
            return render_template(
                "course/import.html",
                form=form,
                universities=universities,
                import_errors=import_errors,
                mapping_headers=mapping_headers,
                mapping_token=mapping_token,
                mapping_format=mapping_format,
                mapping_defaults=mapping_defaults,
                mapping_university_id=mapping_university_id,
                mapping_on_duplicate=mapping_on_duplicate,
                file_extension=file_extension,
            )

        created = skipped = errors = 0
        for idx, row in enumerate(rows, start=2):
            name = row.get("name", "").strip()
            semester = row.get("semester", "").strip()
            if not name or not semester:
                import_errors.append(f"Zeile {idx}: Name oder Semester fehlt.")
                errors += 1
                continue
            try:
                service.add_course(
                    name=name, semester=semester, university_id=university_id
                )
                created += 1
            except IntegrityError:
                db.session.rollback()
                if mapping_on_duplicate == "skip":
                    skipped += 1
                else:
                    import_errors.append(
                        f"Zeile {idx}: Kurs '{name}' ({semester}) existiert bereits."
                    )
                    errors += 1
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
            "course/import.html",
            form=form,
            universities=universities,
            import_errors=import_errors,
            import_summary=import_summary,
        )

    if form.validate_on_submit():
        file = form.file.data
        try:
            token, file_path, extension = save_import_file(file, "courses")
            with file_path.open("rb") as handle:
                stored = FileStorage(stream=handle, filename=file_path.name)
                mapping_headers = load_import_headers(stored, form.file_format.data)
            mapping_token = token
            mapping_format = form.file_format.data
            mapping_on_duplicate = form.on_duplicate.data
            mapping_university_id = str(form.university_id.data)
            normalized = [v for v, _ in mapping_headers]
            mapping_defaults = {
                k: k if k in normalized else "" for k in COURSE_IMPORT_HEADERS
            }
            return render_template(
                "course/import.html",
                form=form,
                universities=universities,
                import_errors=import_errors,
                mapping_headers=mapping_headers,
                mapping_token=mapping_token,
                mapping_format=mapping_format,
                mapping_defaults=mapping_defaults,
                mapping_university_id=mapping_university_id,
                mapping_on_duplicate=mapping_on_duplicate,
                file_extension=extension,
            )
        except ValueError as exc:
            flash(str(exc), "error")

    for _field, errs in form.errors.items():
        for err in errs:
            flash(err, "error")

    return render_template(
        "course/import.html",
        form=form,
        universities=universities,
        import_errors=import_errors,
    )


@bp.route("/<int:course_id>/delete", methods=["GET", "POST"])
@login_required
@admin_required
def delete(course_id: int) -> str | Any:
    """
    Delete a course.

    GET: Show confirmation page
    POST: Delete course and redirect to list

    Args:
        course_id: Course database ID

    Returns:
        Rendered confirmation template (GET) or redirect to list (POST)
    """
    service = CourseService()

    try:
        course = service.get_course(course_id)

        if not course:
            flash(f"Course with ID {course_id} not found.", "error")
            return redirect(url_for("course.index"))

        if request.method == "GET":
            return render_template("course/delete.html", course=course)

        # POST: Delete course using service
        course_name = course.name
        if service.delete_course(course_id):
            flash(f"Course '{course_name}' deleted successfully.", "success")
            return redirect(url_for("course.index"))

        flash(f"Error deleting course '{course_name}'.", "error")
        return redirect(url_for("course.show", course_id=course_id))

    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting course: {e}")
        flash("Error deleting course. Please try again.", "error")
        return redirect(url_for("course.show", course_id=course_id))
