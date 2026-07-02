"""
Enrollment routes blueprint.

This module provides web routes for managing student enrollments in courses.
"""

import logging
from typing import Any

from flask import Blueprint, flash, redirect, request, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.enrollment import VALID_STATUSES
from app.models.student import Student
from app.services.enrollment_service import EnrollmentService

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("enrollment", __name__, url_prefix="/enrollments")


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

    # Parse all student IDs first
    student_id_ints: list[int] = []
    for student_db_id in student_ids:
        try:
            student_id_ints.append(int(student_db_id))
        except ValueError:
            errors += 1

    # Batch-load all requested students in a single query
    students_by_id: dict[int, Student] = {}
    if student_id_ints:
        loaded = (
            service.query(Student)
            .filter(Student.id.in_(student_id_ints))
            .filter(Student.deleted_at.is_(None))
            .all()
        )
        students_by_id = {s.id: s for s in loaded}

    for student_id_int in student_id_ints:
        student = students_by_id.get(student_id_int)
        if not student:
            errors += 1
            continue

        try:
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
