"""
Enrollment routes blueprint.

This module provides web routes for managing student enrollments in courses.
"""

import logging
from typing import Any

from flask_login import login_required
from flask import Blueprint, flash, redirect, request, url_for
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
    Enroll a student in a course.

    Form fields:
        student_id: Student database ID (required)
        course_id: Course database ID (required)
        redirect_to: Where to redirect after enrollment (optional)

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

        # Enroll student using service
        enrollment = service.add_enrollment(student.student_id, course_id_int)

        flash(
            f"{student.first_name} {student.last_name} wurde erfolgreich in "
            f"'{enrollment.course.name}' eingeschrieben.",
            "success",
        )

        # Redirect based on redirect_to parameter
        if redirect_to == "student":
            return redirect(url_for("student.show", student_id=student.id))
        return redirect(url_for("course.show", course_id=enrollment.course.id))

    except ValueError as e:
        flash(str(e), "error")
        return redirect(request.referrer or url_for("index"))

    except IntegrityError:
        flash(
            "Der Studierende ist bereits in diesem Kurs eingeschrieben.",
            "error",
        )
        return redirect(request.referrer or url_for("index"))

    except SQLAlchemyError as e:
        logger.error(f"Database error while enrolling student: {e}")
        flash("Fehler beim Einschreiben. Bitte versuchen Sie es erneut.", "error")
        return redirect(request.referrer or url_for("index"))


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
