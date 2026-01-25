"""
Exam routes blueprint.

This module provides web routes for managing exams through the Flask interface.
"""

import logging
from datetime import date
from typing import Any

from flask_login import login_required
from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.forms.exam import ExamForm
from app.models.course import Course
from app.models.exam import Exam
from app.utils.auth import admin_required
from app.utils.pagination import paginate_query

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("exam", __name__, url_prefix="/exams")


@bp.route("/")
@login_required
def index() -> str:
    """
    List all exams with optional course filter and pagination.

    Query parameters:
        course_id: Optional course filter
        page: Page number (default: 1)

    Returns:
        Rendered template with paginated list of exams
    """
    course_id_param = request.args.get("course_id", "").strip()

    try:
        query = db.session.query(Exam)

        if course_id_param:
            query = query.filter_by(course_id=int(course_id_param))

        query = query.order_by(Exam.exam_date.desc(), Exam.name)
        pagination = paginate_query(query, per_page=20)

        # Get all courses for filter dropdown
        courses = db.session.query(Course).order_by(Course.name).all()

        return render_template(
            "exam/list.html",
            exams=pagination.items,
            pagination=pagination,
            courses=courses,
            course_id=course_id_param,
        )

    except (SQLAlchemyError, ValueError) as e:
        logger.error(f"Error while listing exams: {e}")
        flash("Error loading exams. Please try again.", "error")
        return render_template(
            "exam/list.html",
            exams=[],
            pagination=None,
            courses=[],
            course_id="",
        )


@bp.route("/<int:exam_id>")
@login_required
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
@login_required
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

    form = ExamForm()
    # Cast to int/str for choices to match expectation, ignore List invariance issue
    form.course_id.choices = [(int(c.id), str(c.name)) for c in courses]  # type: ignore

    if form.validate_on_submit():
        try:
            # Create new exam
            exam = Exam(
                name=form.name.data,
                course_id=form.course_id.data,
                exam_date=form.exam_date.data,
                max_points=form.max_points.data,
                weight=form.weight.data,
                description=form.description.data if form.description.data else None,
            )
            db.session.add(exam)
            db.session.commit()

            logger.info(f"Created exam: {exam.name} for course {exam.course_id}")
            flash(f"Exam '{exam.name}' created successfully.", "success")
            return redirect(url_for("exam.show", exam_id=exam.id))

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error while creating exam: {e}")
            flash("Error creating exam. Please try again.", "error")

    # Display form validation errors
    for _field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")

    return render_template("exam/form.html", exam=None, form=form, courses=courses)


@bp.route("/<int:exam_id>/edit", methods=["GET", "POST"])
@login_required
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

        form = ExamForm(obj=exam)
        form.course_id.choices = [(int(c.id), str(c.name)) for c in courses]  # type: ignore

        if form.validate_on_submit():
            try:
                # Update fields - ignore MyPy errors for Column assignment
                exam.name = form.name.data  # type: ignore
                exam.course_id = form.course_id.data  # type: ignore
                exam.exam_date = form.exam_date.data  # type: ignore
                exam.max_points = form.max_points.data  # type: ignore
                exam.weight = form.weight.data  # type: ignore
                exam.description = form.description.data or None  # type: ignore

                db.session.commit()
                logger.info(f"Updated exam: {exam.name} for course {exam.course_id}")
                flash(f"Exam '{exam.name}' updated successfully.", "success")
                return redirect(url_for("exam.show", exam_id=exam.id))

            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database error while updating exam: {e}")
                flash("Error updating exam. Please try again.", "error")

        # Display form validation errors
        for _field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("exam/form.html", exam=exam, form=form, courses=courses)

    except SQLAlchemyError as e:
        logger.error(f"Database error while loading exam: {e}")
        flash("Error loading exam. Please try again.", "error")
        return redirect(url_for("exam.index"))


@bp.route("/<int:exam_id>/delete", methods=["GET", "POST"])
@login_required
@admin_required
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