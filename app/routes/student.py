"""
Student routes blueprint.

This module provides web routes for managing students through the Flask interface.
"""

import logging
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

from app.forms.student import StudentForm
from app.models.student import Student
from app.services.student_service import StudentService
from app.utils.pagination import paginate_query

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("student", __name__, url_prefix="/students")


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
        query = service.query(Student)

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
            flash(f"Student with ID {student_id} not found.", "error")
            return redirect(url_for("student.index"))

        return render_template("student/detail.html", student=student)

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
            flash(f"Student with ID {student_id} not found.", "error")
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
            flash(f"Student with ID {student_id} not found.", "error")
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
