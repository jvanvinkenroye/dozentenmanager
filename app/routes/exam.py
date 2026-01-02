"""
Exam routes blueprint.

This module provides web routes for managing exams through the Flask interface.
"""

import logging
from datetime import datetime
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models.course import Course
from app.models.exam import Exam, validate_max_points, validate_weight

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("exam", __name__, url_prefix="/exams")


@bp.route("/")
def index() -> str:
    """
    List all exams with optional course filter.

    Query parameters:
        course_id: Optional course filter

    Returns:
        Rendered template with list of exams
    """
    course_id_param = request.args.get("course_id", "").strip()

    try:
        query = db.session.query(Exam)

        if course_id_param:
            query = query.filter_by(course_id=int(course_id_param))

        exams = query.order_by(Exam.exam_date.desc(), Exam.name).all()

        # Get all courses for filter dropdown
        courses = db.session.query(Course).order_by(Course.name).all()

        return render_template(
            "exam/list.html",
            exams=exams,
            courses=courses,
            course_id=course_id_param,
        )

    except (SQLAlchemyError, ValueError) as e:
        logger.error(f"Error while listing exams: {e}")
        flash("Error loading exams. Please try again.", "error")
        return render_template(
            "exam/list.html",
            exams=[],
            courses=[],
            course_id="",
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
        exam = db.session.query(Exam).filter_by(id=exam_id).first()

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
        course_id: Course ID (required)
        exam_date: Exam date (required, format: YYYY-MM-DD)
        max_points: Maximum achievable points (required)
        weight: Weight percentage (default: 100)
        description: Optional description

    Returns:
        Rendered form template (GET) or redirect to detail page (POST)
    """
    # Get courses for dropdown
    try:
        courses = db.session.query(Course).order_by(Course.name).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while loading courses: {e}")
        flash("Error loading courses. Please try again.", "error")
        return redirect(url_for("exam.index"))

    if request.method == "GET":
        return render_template("exam/form.html", exam=None, courses=courses)

    # POST: Create exam
    name = request.form.get("name", "").strip()
    course_id_str = request.form.get("course_id", "").strip()
    exam_date_str = request.form.get("exam_date", "").strip()
    max_points_str = request.form.get("max_points", "").strip()
    weight_str = request.form.get("weight", "100").strip()
    description = request.form.get("description", "").strip()

    # Validate required fields
    if not name:
        flash("Exam name is required.", "error")
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

    if not exam_date_str:
        flash("Exam date is required.", "error")
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

    # Parse and validate fields
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

    try:
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date format. Use YYYY-MM-DD (e.g., 2024-06-15).", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    try:
        max_points = float(max_points_str)
    except ValueError:
        flash("Maximum points must be a number.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    try:
        weight = float(weight_str)
    except ValueError:
        flash("Weight must be a number.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    # Validate business rules
    if not validate_max_points(max_points):
        flash("Maximum points must be greater than 0.", "error")
        return render_template(
            "exam/form.html",
            exam=None,
            courses=courses,
            form_data=request.form,
        )

    if not validate_weight(weight):
        flash("Weight must be between 0 and 100.", "error")
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
            course_id=course_id,
            exam_date=exam_date,
            max_points=max_points,
            weight=weight,
            description=description if description else None,
        )
        db.session.add(exam)
        db.session.commit()

        flash(f"Exam '{exam.name}' created successfully.", "success")
        return redirect(url_for("exam.show", exam_id=exam.id))

    except SQLAlchemyError as e:
        db.session.rollback()
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
        course_id: Course ID (required)
        exam_date: Exam date (required)
        max_points: Maximum points (required)
        weight: Weight percentage (required)
        description: Optional description

    Returns:
        Rendered form template (GET) or redirect to detail page (POST)
    """
    try:
        exam = db.session.query(Exam).filter_by(id=exam_id).first()

        if not exam:
            flash(f"Exam with ID {exam_id} not found.", "error")
            return redirect(url_for("exam.index"))

        # Get courses for dropdown
        courses = db.session.query(Course).order_by(Course.name).all()

        if request.method == "GET":
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
            )

        # POST: Update exam
        name = request.form.get("name", "").strip()
        course_id_str = request.form.get("course_id", "").strip()
        exam_date_str = request.form.get("exam_date", "").strip()
        max_points_str = request.form.get("max_points", "").strip()
        weight_str = request.form.get("weight", "").strip()
        description = request.form.get("description", "").strip()

        # Validate required fields
        if not name:
            flash("Exam name is required.", "error")
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

        if not exam_date_str:
            flash("Exam date is required.", "error")
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

        # Parse and validate fields
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

        try:
            exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD (e.g., 2024-06-15).", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        try:
            max_points = float(max_points_str)
        except ValueError:
            flash("Maximum points must be a number.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        try:
            weight = float(weight_str)
        except ValueError:
            flash("Weight must be a number.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        # Validate business rules
        if not validate_max_points(max_points):
            flash("Maximum points must be greater than 0.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        if not validate_weight(weight):
            flash("Weight must be between 0 and 100.", "error")
            return render_template(
                "exam/form.html",
                exam=exam,
                courses=courses,
                form_data=request.form,
            )

        # Update fields
        exam.name = name
        exam.course_id = course_id
        exam.exam_date = exam_date
        exam.max_points = max_points
        exam.weight = weight
        exam.description = description if description else None

        db.session.commit()
        flash(f"Exam '{exam.name}' updated successfully.", "success")
        return redirect(url_for("exam.show", exam_id=exam.id))

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while updating exam: {e}")
        flash("Error updating exam. Please try again.", "error")
        return render_template(
            "exam/form.html",
            exam=exam,
            courses=courses,
            form_data=request.form,
        )


@bp.route("/<int:exam_id>/delete", methods=["GET", "POST"])
def delete(exam_id: int) -> str | Any:
    """
    Delete an exam.

    GET: Show confirmation page
    POST: Delete exam and redirect to list

    Args:
        exam_id: Exam database ID

    Returns:
        Rendered confirmation template (GET) or redirect to list (POST)
    """
    try:
        exam = db.session.query(Exam).filter_by(id=exam_id).first()

        if not exam:
            flash(f"Exam with ID {exam_id} not found.", "error")
            return redirect(url_for("exam.index"))

        if request.method == "GET":
            return render_template("exam/delete.html", exam=exam)

        # POST: Delete exam
        exam_name = exam.name
        db.session.delete(exam)
        db.session.commit()

        flash(f"Exam '{exam_name}' deleted successfully.", "success")
        return redirect(url_for("exam.index"))

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while deleting exam: {e}")
        flash("Error deleting exam. Please try again.", "error")
        return redirect(url_for("exam.show", exam_id=exam_id))
