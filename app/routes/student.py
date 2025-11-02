"""
Student routes blueprint.

This module provides web routes for managing students through the Flask interface.
"""

import logging
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

import app as app_module
from app.models.student import Student, validate_email, validate_student_id

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("student", __name__, url_prefix="/students")


@bp.route("/")
def index() -> str:
    """
    List all students with optional search and program filter.

    Query parameters:
        search: Optional search term to filter by name, student_id, or email
        program: Optional program filter

    Returns:
        Rendered template with list of students
    """
    search_term = request.args.get("search", "").strip()
    program_filter = request.args.get("program", "").strip()

    try:
        query = app_module.db_session.query(Student)  # type: ignore[union-attr]

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

        return render_template(
            "student/list.html",
            students=students,
            search_term=search_term,
            program_filter=program_filter,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing students: {e}")
        flash("Error loading students. Please try again.", "error")
        return render_template(
            "student/list.html",
            students=[],
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
    try:
        student = (
            app_module.db_session.query(Student)  # type: ignore[union-attr]
            .filter_by(id=student_id)
            .first()
        )

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
    if request.method == "GET":
        return render_template("student/form.html", student=None)

    # POST: Create student
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    student_id_value = request.form.get("student_id", "").strip()
    email = request.form.get("email", "").strip()
    program = request.form.get("program", "").strip()

    # Validate required fields
    if not first_name:
        flash("First name is required.", "error")
        return render_template(
            "student/form.html", student=None, form_data=request.form
        )

    if not last_name:
        flash("Last name is required.", "error")
        return render_template(
            "student/form.html", student=None, form_data=request.form
        )

    if not student_id_value:
        flash("Student ID is required.", "error")
        return render_template(
            "student/form.html", student=None, form_data=request.form
        )

    if not validate_student_id(student_id_value):
        flash("Invalid student ID format. Must be exactly 8 digits.", "error")
        return render_template(
            "student/form.html", student=None, form_data=request.form
        )

    if not email:
        flash("Email is required.", "error")
        return render_template(
            "student/form.html", student=None, form_data=request.form
        )

    if not validate_email(email):
        flash("Invalid email format.", "error")
        return render_template(
            "student/form.html", student=None, form_data=request.form
        )

    if not program:
        flash("Program is required.", "error")
        return render_template(
            "student/form.html", student=None, form_data=request.form
        )

    try:
        # Create new student
        student = Student(
            first_name=first_name,
            last_name=last_name,
            student_id=student_id_value,
            email=email.lower(),
            program=program,
        )
        app_module.db_session.add(student)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(
            f"Student '{student.first_name} {student.last_name}' created successfully.",
            "success",
        )
        return redirect(url_for("student.show", student_id=student.id))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while creating student: {e}")

        # Check for unique constraint violations
        if "student_id" in str(e):
            flash(f"Student with ID '{student_id_value}' already exists.", "error")
        elif "email" in str(e):
            flash(f"Student with email '{email}' already exists.", "error")
        else:
            flash("Error creating student. Please try again.", "error")

        return render_template(
            "student/form.html", student=None, form_data=request.form
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
    try:
        student = (
            app_module.db_session.query(Student)  # type: ignore[union-attr]
            .filter_by(id=student_id)
            .first()
        )

        if not student:
            flash(f"Student with ID {student_id} not found.", "error")
            return redirect(url_for("student.index"))

        if request.method == "GET":
            return render_template("student/form.html", student=student)

        # POST: Update student
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        student_id_value = request.form.get("student_id", "").strip()
        email = request.form.get("email", "").strip()
        program = request.form.get("program", "").strip()

        # Validate inputs
        if not first_name:
            flash("First name is required.", "error")
            return render_template(
                "student/form.html", student=student, form_data=request.form
            )

        if not last_name:
            flash("Last name is required.", "error")
            return render_template(
                "student/form.html", student=student, form_data=request.form
            )

        if not student_id_value:
            flash("Student ID is required.", "error")
            return render_template(
                "student/form.html", student=student, form_data=request.form
            )

        if not validate_student_id(student_id_value):
            flash("Invalid student ID format. Must be exactly 8 digits.", "error")
            return render_template(
                "student/form.html", student=student, form_data=request.form
            )

        if not email:
            flash("Email is required.", "error")
            return render_template(
                "student/form.html", student=student, form_data=request.form
            )

        if not validate_email(email):
            flash("Invalid email format.", "error")
            return render_template(
                "student/form.html", student=student, form_data=request.form
            )

        if not program:
            flash("Program is required.", "error")
            return render_template(
                "student/form.html", student=student, form_data=request.form
            )

        # Update fields
        student.first_name = first_name
        student.last_name = last_name
        student.student_id = student_id_value
        student.email = email.lower()
        student.program = program

        app_module.db_session.commit()  # type: ignore[union-attr]
        flash(
            f"Student '{student.first_name} {student.last_name}' updated successfully.",
            "success",
        )
        return redirect(url_for("student.show", student_id=student.id))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating student: {e}")

        # Check for unique constraint violations
        if "student_id" in str(e):
            flash(f"Student with ID '{student_id_value}' already exists.", "error")
        elif "email" in str(e):
            flash(f"Student with email '{email}' already exists.", "error")
        else:
            flash("Error updating student. Please try again.", "error")

        return render_template(
            "student/form.html", student=student, form_data=request.form
        )


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
    try:
        student = (
            app_module.db_session.query(Student)  # type: ignore[union-attr]
            .filter_by(id=student_id)
            .first()
        )

        if not student:
            flash(f"Student with ID {student_id} not found.", "error")
            return redirect(url_for("student.index"))

        if request.method == "GET":
            return render_template("student/delete.html", student=student)

        # POST: Delete student
        student_name = f"{student.first_name} {student.last_name}"
        app_module.db_session.delete(student)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(f"Student '{student_name}' deleted successfully.", "success")
        return redirect(url_for("student.index"))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting student: {e}")
        flash("Error deleting student. Please try again.", "error")
        return redirect(url_for("student.show", student_id=student_id))
