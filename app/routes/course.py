"""
Course routes blueprint.

This module provides web routes for managing courses through the Flask interface.
"""

import logging
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

import app as app_module
from app.models.course import Course, generate_slug, validate_semester
from app.models.student import Student
from app.models.university import University

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("course", __name__, url_prefix="/courses")


@bp.route("/")
def index() -> str:
    """
    List all courses with optional search and filters.

    Query parameters:
        search: Optional search term to filter by name
        university_id: Optional university filter
        semester: Optional semester filter

    Returns:
        Rendered template with list of courses
    """
    search_term = request.args.get("search", "").strip()
    university_id = request.args.get("university_id", "").strip()
    semester_filter = request.args.get("semester", "").strip()

    try:
        query = app_module.db_session.query(Course)  # type: ignore[union-attr]

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(Course.name.ilike(search_pattern))

        if university_id:
            query = query.filter_by(university_id=int(university_id))

        if semester_filter:
            query = query.filter_by(semester=semester_filter)

        courses = query.order_by(Course.semester.desc(), Course.name).all()

        # Get all universities for filter dropdown
        universities = (
            app_module.db_session.query(University)  # type: ignore[union-attr]
            .order_by(University.name)
            .all()
        )

        return render_template(
            "course/list.html",
            courses=courses,
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
            universities=[],
            search_term="",
            university_id="",
            semester_filter="",
        )


@bp.route("/<int:course_id>")
def show(course_id: int) -> str | Any:
    """
    Show details for a specific course.

    Args:
        course_id: Course database ID

    Returns:
        Rendered template with course details or redirect
    """
    try:
        from app.models.enrollment import Enrollment

        course = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .filter_by(id=course_id)
            .first()
        )

        if not course:
            flash(f"Course with ID {course_id} not found.", "error")
            return redirect(url_for("course.index"))

        # Get enrollments for this course
        enrollments = (
            app_module.db_session.query(Enrollment)  # type: ignore[union-attr]
            .filter_by(course_id=course_id)
            .all()
        )

        # Get all students for enrollment dropdown (students not already enrolled)
        enrolled_student_ids = [e.student_id for e in enrollments]
        available_students = (
            app_module.db_session.query(Student)  # type: ignore[union-attr]
            .filter(
                ~Student.id.in_(enrolled_student_ids) if enrolled_student_ids else True  # type: ignore[arg-type]
            )
            .order_by(Student.last_name, Student.first_name)
            .all()
        )

        return render_template(
            "course/detail.html",
            course=course,
            enrollments=enrollments,
            available_students=available_students,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching course: {e}")
        flash("Error loading course details. Please try again.", "error")
        return redirect(url_for("course.index"))


@bp.route("/new", methods=["GET", "POST"])
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
    # Get universities for dropdown
    try:
        universities = (
            app_module.db_session.query(University)  # type: ignore[union-attr]
            .order_by(University.name)
            .all()
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while loading universities: {e}")
        flash("Error loading universities. Please try again.", "error")
        return redirect(url_for("course.index"))

    if request.method == "GET":
        return render_template(
            "course/form.html", course=None, universities=universities
        )

    # POST: Create course
    name = request.form.get("name", "").strip()
    semester = request.form.get("semester", "").strip()
    university_id_str = request.form.get("university_id", "").strip()
    slug = request.form.get("slug", "").strip()

    # Validate required fields
    if not name:
        flash("Course name is required.", "error")
        return render_template(
            "course/form.html",
            course=None,
            universities=universities,
            form_data=request.form,
        )

    if not semester:
        flash("Semester is required.", "error")
        return render_template(
            "course/form.html",
            course=None,
            universities=universities,
            form_data=request.form,
        )

    if not validate_semester(semester):
        flash(
            "Invalid semester format. Must be YYYY_SoSe or YYYY_WiSe (e.g., 2023_SoSe, 2024_WiSe)",
            "error",
        )
        return render_template(
            "course/form.html",
            course=None,
            universities=universities,
            form_data=request.form,
        )

    if not university_id_str:
        flash("University is required.", "error")
        return render_template(
            "course/form.html",
            course=None,
            universities=universities,
            form_data=request.form,
        )

    try:
        university_id = int(university_id_str)
    except ValueError:
        flash("Invalid university selection.", "error")
        return render_template(
            "course/form.html",
            course=None,
            universities=universities,
            form_data=request.form,
        )

    # Generate slug if not provided
    if not slug:
        slug = generate_slug(name)

    try:
        # Create new course
        course = Course(
            name=name,
            semester=semester,
            university_id=university_id,
            slug=slug,
        )
        app_module.db_session.add(course)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(f"Course '{course.name}' created successfully.", "success")
        return redirect(url_for("course.show", course_id=course.id))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while creating course: {e}")

        # Check for unique constraint violations
        if "uq_course_university_semester_slug" in str(e).lower():
            flash(
                f"Course with slug '{slug}' already exists for this university in semester {semester}.",
                "error",
            )
        else:
            flash("Error creating course. Please try again.", "error")

        return render_template(
            "course/form.html",
            course=None,
            universities=universities,
            form_data=request.form,
        )


@bp.route("/<int:course_id>/edit", methods=["GET", "POST"])
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
    try:
        course = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .filter_by(id=course_id)
            .first()
        )

        if not course:
            flash(f"Course with ID {course_id} not found.", "error")
            return redirect(url_for("course.index"))

        # Get universities for dropdown
        universities = (
            app_module.db_session.query(University)  # type: ignore[union-attr]
            .order_by(University.name)
            .all()
        )

        if request.method == "GET":
            return render_template(
                "course/form.html", course=course, universities=universities
            )

        # POST: Update course
        name = request.form.get("name", "").strip()
        semester = request.form.get("semester", "").strip()
        university_id_str = request.form.get("university_id", "").strip()
        slug = request.form.get("slug", "").strip()

        # Validate inputs
        if not name:
            flash("Course name is required.", "error")
            return render_template(
                "course/form.html",
                course=course,
                universities=universities,
                form_data=request.form,
            )

        if not semester:
            flash("Semester is required.", "error")
            return render_template(
                "course/form.html",
                course=course,
                universities=universities,
                form_data=request.form,
            )

        if not validate_semester(semester):
            flash(
                "Invalid semester format. Must be YYYY_SoSe or YYYY_WiSe",
                "error",
            )
            return render_template(
                "course/form.html",
                course=course,
                universities=universities,
                form_data=request.form,
            )

        if not university_id_str:
            flash("University is required.", "error")
            return render_template(
                "course/form.html",
                course=course,
                universities=universities,
                form_data=request.form,
            )

        try:
            university_id = int(university_id_str)
        except ValueError:
            flash("Invalid university selection.", "error")
            return render_template(
                "course/form.html",
                course=course,
                universities=universities,
                form_data=request.form,
            )

        # Update fields
        course.name = name
        course.semester = semester
        course.university_id = university_id

        # Update slug if provided, otherwise regenerate
        if slug:
            course.slug = slug
        else:
            course.slug = generate_slug(name)

        app_module.db_session.commit()  # type: ignore[union-attr]
        flash(f"Course '{course.name}' updated successfully.", "success")
        return redirect(url_for("course.show", course_id=course.id))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating course: {e}")

        # Check for unique constraint violations
        if "uq_course_university_semester_slug" in str(e).lower():
            flash(
                f"Course with slug '{course.slug}' already exists for this university in semester {semester}.",  # type: ignore[union-attr]
                "error",
            )
        else:
            flash("Error updating course. Please try again.", "error")

        return render_template(
            "course/form.html",
            course=course,
            universities=universities,
            form_data=request.form,
        )


@bp.route("/<int:course_id>/delete", methods=["GET", "POST"])
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
    try:
        course = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .filter_by(id=course_id)
            .first()
        )

        if not course:
            flash(f"Course with ID {course_id} not found.", "error")
            return redirect(url_for("course.index"))

        if request.method == "GET":
            return render_template("course/delete.html", course=course)

        # POST: Delete course
        course_name = course.name
        app_module.db_session.delete(course)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(f"Course '{course_name}' deleted successfully.", "success")
        return redirect(url_for("course.index"))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting course: {e}")
        flash("Error deleting course. Please try again.", "error")
        return redirect(url_for("course.show", course_id=course_id))
