"""
Enrollment routes blueprint.

This module provides web routes for managing student enrollments in courses.
"""

import logging
from datetime import date
from typing import Any

from flask import Blueprint, flash, redirect, request, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import app as app_module
from app.models.course import Course
from app.models.enrollment import VALID_STATUSES, Enrollment
from app.models.student import Student

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("enrollment", __name__, url_prefix="/enrollments")


@bp.route("/enroll", methods=["POST"])
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
    student_id = request.form.get("student_id", "").strip()
    course_id = request.form.get("course_id", "").strip()
    redirect_to = request.form.get("redirect_to", "").strip()

    # Validate inputs
    if not student_id or not course_id:
        flash("Student and course are required.", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        student_id_int = int(student_id)
        course_id_int = int(course_id)
    except ValueError:
        flash("Invalid student or course ID.", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        # Verify student exists
        student = (
            app_module.db_session.query(Student)  # type: ignore[union-attr]
            .filter_by(id=student_id_int)
            .first()
        )
        if not student:
            flash("Student not found.", "error")
            return redirect(request.referrer or url_for("index"))

        # Verify course exists
        course = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .filter_by(id=course_id_int)
            .first()
        )
        if not course:
            flash("Course not found.", "error")
            return redirect(request.referrer or url_for("index"))

        # Create enrollment
        enrollment = Enrollment(
            student_id=student_id_int,
            course_id=course_id_int,
            status="active",
        )
        app_module.db_session.add(enrollment)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(
            f"{student.first_name} {student.last_name} wurde erfolgreich in "
            f"'{course.name}' eingeschrieben.",
            "success",
        )

        # Redirect based on redirect_to parameter
        if redirect_to == "student":
            return redirect(url_for("student.show", student_id=student.student_id))
        else:
            return redirect(url_for("course.show", course_id=course.id))

    except IntegrityError:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        flash(
            "Der Studierende ist bereits in diesem Kurs eingeschrieben.",
            "error",
        )
        return redirect(request.referrer or url_for("index"))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while enrolling student: {e}")
        flash("Fehler beim Einschreiben. Bitte versuchen Sie es erneut.", "error")
        return redirect(request.referrer or url_for("index"))


@bp.route("/unenroll", methods=["POST"])
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
    student_id = request.form.get("student_id", "").strip()
    course_id = request.form.get("course_id", "").strip()
    redirect_to = request.form.get("redirect_to", "").strip()

    # Validate inputs
    if not student_id or not course_id:
        flash("Student and course are required.", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        student_id_int = int(student_id)
        course_id_int = int(course_id)
    except ValueError:
        flash("Invalid student or course ID.", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        # Find enrollment
        enrollment = (
            app_module.db_session.query(Enrollment)  # type: ignore[union-attr]
            .filter_by(student_id=student_id_int, course_id=course_id_int)
            .first()
        )

        if not enrollment:
            flash("Einschreibung nicht gefunden.", "error")
            return redirect(request.referrer or url_for("index"))

        # Get names before deleting
        student_name = f"{enrollment.student.first_name} {enrollment.student.last_name}"
        course_name = enrollment.course.name
        student_student_id = enrollment.student.student_id

        app_module.db_session.delete(enrollment)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(
            f"{student_name} wurde erfolgreich aus '{course_name}' ausgetragen.",
            "success",
        )

        # Redirect based on redirect_to parameter
        if redirect_to == "student":
            return redirect(url_for("student.show", student_id=student_student_id))
        else:
            return redirect(url_for("course.show", course_id=course_id_int))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while unenrolling student: {e}")
        flash("Fehler beim Austragen. Bitte versuchen Sie es erneut.", "error")
        return redirect(request.referrer or url_for("index"))


@bp.route("/status", methods=["POST"])
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
    student_id = request.form.get("student_id", "").strip()
    course_id = request.form.get("course_id", "").strip()
    status = request.form.get("status", "").strip()
    redirect_to = request.form.get("redirect_to", "").strip()

    # Validate inputs
    if not student_id or not course_id or not status:
        flash("Student, course, and status are required.", "error")
        return redirect(request.referrer or url_for("index"))

    if status not in VALID_STATUSES:
        flash(f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        student_id_int = int(student_id)
        course_id_int = int(course_id)
    except ValueError:
        flash("Invalid student or course ID.", "error")
        return redirect(request.referrer or url_for("index"))

    try:
        # Find enrollment
        enrollment = (
            app_module.db_session.query(Enrollment)  # type: ignore[union-attr]
            .filter_by(student_id=student_id_int, course_id=course_id_int)
            .first()
        )

        if not enrollment:
            flash("Einschreibung nicht gefunden.", "error")
            return redirect(request.referrer or url_for("index"))

        old_status = enrollment.status
        enrollment.status = status

        # Set unenrollment date when status changes to dropped
        if status == "dropped" and not enrollment.unenrollment_date:
            enrollment.unenrollment_date = date.today()

        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(
            f"Status wurde von '{old_status}' auf '{status}' aktualisiert.",
            "success",
        )

        # Redirect based on redirect_to parameter
        if redirect_to == "student":
            return redirect(
                url_for("student.show", student_id=enrollment.student.student_id)
            )
        else:
            return redirect(url_for("course.show", course_id=course_id_int))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating enrollment status: {e}")
        flash(
            "Fehler beim Aktualisieren des Status. Bitte versuchen Sie es erneut.",
            "error",
        )
        return redirect(request.referrer or url_for("index"))
