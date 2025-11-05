"""
Exam routes blueprint.

This module provides web routes for managing exams through the Flask interface.
"""

import logging
from datetime import datetime
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

import app as app_module
from app.models.course import Course
from app.models.exam import Exam, validate_weight, validate_max_points

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("exam", __name__, url_prefix="/exams")


@bp.route("/")
def index() -> str:
    """
    List all exams with optional search and filters.

    Query parameters:
        search: Optional search term to filter by name
        course_id: Optional course filter
        exam_type: Optional exam type filter

    Returns:
        Rendered template with list of exams
    """
    search_term = request.args.get("search", "").strip()
    course_id = request.args.get("course_id", "").strip()
    exam_type_filter = request.args.get("exam_type", "").strip()

    try:
        query = app_module.db_session.query(Exam)  # type: ignore[union-attr]

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(Exam.name.ilike(search_pattern))

        if course_id:
            query = query.filter_by(course_id=int(course_id))

        if exam_type_filter:
            query = query.filter_by(exam_type=exam_type_filter.lower())

        exams = query.order_by(Exam.due_date.asc(), Exam.name).all()

        # Get all courses for filter dropdown
        courses = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .order_by(Course.semester.desc(), Course.name)
            .all()
        )

        return render_template(
            "exam/list.html",
            exams=exams,
            courses=courses,
            search_term=search_term,
            course_id=course_id,
            exam_type_filter=exam_type_filter,
        )

    except (SQLAlchemyError, ValueError) as e:
        logger.error(f"Error while listing exams: {e}")
        flash("Error loading exams. Please try again.", "error")
        return render_template(
            "exam/list.html",
            exams=[],
            courses=[],
            search_term="",
            course_id="",
            exam_type_filter="",
        )


@bp.route("/<int:exam_id>")
def show(exam_id: int) -> str | Any:
    """
    Show details for a specific exam.

    Args:
        exam_id: Exam database ID

    Returns:
        Rendered template with exam details or redirect
    """
    try:
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )

        if not exam:
            flash(f"Exam with ID {exam_id} not found.", "error")
            return redirect(url_for("exam.index"))

        return render_template(
            "exam/detail.html",
            exam=exam,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching exam: {e}")
        flash("Error loading exam details. Please try again.", "error")
        return redirect(url_for("exam.index"))


@bp.route("/new", methods=["GET", "POST"])
def new() -> str | Any:
    """
    Create a new exam.

    GET: Show form
    POST: Create exam and redirect to detail page

    Form fields:
        name: Exam name (required)
        exam_type: Exam type (required)
        max_points: Maximum points (required)
        weight: Weight in final grade (required, 0-1)
        course_id: Course ID (required)
        due_date: Due date (optional, format: YYYY-MM-DD or YYYY-MM-DD HH:MM)

    Returns:
        Rendered form template (GET) or redirect to detail page (POST)
    """
    # Get courses for dropdown
    try:
        courses = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .order_by(Course.semester.desc(), Course.name)
            .all()
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while loading courses: {e}")
        flash("Error loading courses. Please try again.", "error")
        return redirect(url_for("exam.index"))

    if request.method == "GET":
        return render_template("exam/form.html", exam=None, courses=courses)

    # POST: Create exam
    name = request.form.get("name", "").strip()
    exam_type = request.form.get("exam_type", "").strip()
    max_points_str = request.form.get("max_points", "").strip()
    weight_str = request.form.get("weight", "").strip()
    course_id_str = request.form.get("course_id", "").strip()
    due_date_str = request.form.get("due_date", "").strip()

    # Validate required fields
    if not name:
        flash("Exam name is required.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    if not exam_type:
        flash("Exam type is required.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    if not max_points_str:
        flash("Maximum points is required.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    if not weight_str:
        flash("Weight is required.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    if not course_id_str:
        flash("Course is required.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    # Parse and validate numeric fields
    try:
        max_points = float(max_points_str)
        if not validate_max_points(max_points):
            flash("Maximum points must be a positive number.", "error")
            return render_template(
                "exam/form.html",
                exam=None,
                courses=courses,
                form_data=request.form,
            )
    except ValueError:
        flash("Invalid maximum points value.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    try:
        weight = float(weight_str)
        if not validate_weight(weight):
            flash("Weight must be between 0 and 1 (e.g., 0.3 for 30%).", "error")
            return render_template(
                "exam/form.html",
                exam=None,
                courses=courses,
                form_data=request.form,
            )
    except ValueError:
        flash("Invalid weight value.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    try:
        course_id = int(course_id_str)
    except ValueError:
        flash("Invalid course selection.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    # Parse due date if provided
    due_date = None
    if due_date_str:
        try:
            # Try parsing with time first (datetime-local format from HTML5)
            if "T" in due_date_str:
                due_date = datetime.fromisoformat(due_date_str.replace("T", " "))
            else:
                # Try parsing date only
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "error")
            return render_template(
                "exam/form.html",
                exam=None,
                courses=courses,
                form_data=request.form,
            )

    try:
        # Create new exam
        exam = Exam(
            name=name,
            exam_type=exam_type.lower(),
            max_points=max_points,
            weight=weight,
            course_id=course_id,
            due_date=due_date,
        )
        app_module.db_session.add(exam)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(f"Exam '{exam.name}' created successfully.", "success")
        return redirect(url_for("exam.show", exam_id=exam.id))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while creating exam: {e}")
        flash("Error creating exam. Please try again.", "error")

        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )


@bp.route("/<int:exam_id>/edit", methods=["GET", "POST"])
def edit(exam_id: int) -> str | Any:
    """
    Edit an existing exam.

    GET: Show edit form
    POST: Update exam and redirect to detail page

    Args:
        exam_id: Exam database ID

    Form fields:
        name: Exam name (required)
        exam_type: Exam type (required)
        max_points: Maximum points (required)
        weight: Weight in final grade (required)
        course_id: Course ID (required)
        due_date: Due date (optional)

    Returns:
        Rendered form template (GET) or redirect to detail page (POST)
    """
    try:
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )

        if not exam:
            flash(f"Exam with ID {exam_id} not found.", "error")
            return redirect(url_for("exam.index"))

        # Get courses for dropdown
        courses = (
            app_module.db_session.query(Course)  # type: ignore[union-attr]
            .order_by(Course.semester.desc(), Course.name)
            .all()
        )

        if request.method == "GET":
            return render_template("exam/form.html", exam=exam, courses=courses)

        # POST: Update exam
        name = request.form.get("name", "").strip()
        exam_type = request.form.get("exam_type", "").strip()
        max_points_str = request.form.get("max_points", "").strip()
        weight_str = request.form.get("weight", "").strip()
        course_id_str = request.form.get("course_id", "").strip()
        due_date_str = request.form.get("due_date", "").strip()

        # Validate required fields
        if not name:
            flash("Exam name is required.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        if not exam_type:
            flash("Exam type is required.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        if not max_points_str:
            flash("Maximum points is required.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        if not weight_str:
            flash("Weight is required.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        if not course_id_str:
            flash("Course is required.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        # Parse and validate numeric fields
        try:
            max_points = float(max_points_str)
            if not validate_max_points(max_points):
                flash("Maximum points must be a positive number.", "error")
                return render_template(
                    "exam/form.html",
                    exam=exam,
                    courses=courses,
                    form_data=request.form,
                )
        except ValueError:
            flash("Invalid maximum points value.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        try:
            weight = float(weight_str)
            if not validate_weight(weight):
                flash("Weight must be between 0 and 1 (e.g., 0.3 for 30%).", "error")
                return render_template(
                    "exam/form.html",
                    exam=exam,
                    courses=courses,
                    form_data=request.form,
                )
        except ValueError:
            flash("Invalid weight value.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        try:
            course_id = int(course_id_str)
        except ValueError:
            flash("Invalid course selection.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        # Parse due date if provided
        due_date = None
        if due_date_str:
            try:
                # Try parsing with time first (datetime-local format from HTML5)
                if "T" in due_date_str:
                    due_date = datetime.fromisoformat(due_date_str.replace("T", " "))
                else:
                    # Try parsing date only
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                flash("Invalid date format. Use YYYY-MM-DD.", "error")
                return render_template(
                    "exam/form.html",
                    exam=exam,
                    courses=courses,
                    form_data=request.form,
                )

        # Update exam fields
        exam.name = name
        exam.exam_type = exam_type.lower()
        exam.max_points = max_points
        exam.weight = weight
        exam.course_id = course_id
        exam.due_date = due_date

        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(f"Exam '{exam.name}' updated successfully.", "success")
        return redirect(url_for("exam.show", exam_id=exam.id))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating exam: {e}")
        flash("Error updating exam. Please try again.", "error")

        return render_template(
            "exam/form.html",
            exam=exam,
            courses=courses,
            form_data=request.form,
        )


@bp.route("/<int:exam_id>/delete", methods=["POST"])
def delete(exam_id: int) -> Any:
    """
    Delete an exam.

    Args:
        exam_id: Exam database ID

    Returns:
        Redirect to exam list
    """
    try:
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )

        if not exam:
            flash(f"Exam with ID {exam_id} not found.", "error")
            return redirect(url_for("exam.index"))

        exam_name = exam.name
        app_module.db_session.delete(exam)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(f"Exam '{exam_name}' deleted successfully.", "success")
        return redirect(url_for("exam.index"))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting exam: {e}")
        flash("Error deleting exam. Please try again.", "error")
        return redirect(url_for("exam.show", exam_id=exam_id))
