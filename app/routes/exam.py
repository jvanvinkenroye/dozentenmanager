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
from app.models.exam_component import ExamComponent
from cli.exam_component_cli import (
    add_component,
    update_component,
    delete_component as delete_component_cli,
    calculate_weight_stats,
)

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

        # Get components for this exam, ordered by display order
        components = (
            app_module.db_session.query(ExamComponent)  # type: ignore[union-attr]
            .filter_by(exam_id=exam_id)
            .order_by(ExamComponent.order)
            .all()
        )

        # Calculate weight statistics from components list (avoids redundant queries)
        is_valid, total_weight, available_weight = calculate_weight_stats(components)

        return render_template(
            "exam/detail.html",
            exam=exam,
            components=components,
            total_weight=total_weight,
            is_valid_weight=is_valid,
            available_weight=available_weight,
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


# ==================== Exam Component Routes ====================


@bp.route("/<int:exam_id>/components/add", methods=["POST"])
def add_exam_component(exam_id: int) -> Any:
    """
    Add a new component to an exam.

    Args:
        exam_id: Exam database ID

    Form fields:
        name: Component name (required)
        description: Component description (optional)
        max_points: Maximum points (required)
        weight: Weight in exam grade (required, 0-1)
        order: Display order (optional, defaults to 0)

    Returns:
        Redirect to exam detail page
    """
    try:
        # Verify exam exists
        exam = (
            app_module.db_session.query(Exam)  # type: ignore[union-attr]
            .filter_by(id=exam_id)
            .first()
        )

        if not exam:
            flash(f"Prüfung mit ID {exam_id} nicht gefunden.", "error")
            return redirect(url_for("exam.index"))

        # Get form data
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip() or None
        max_points_str = request.form.get("max_points", "").strip()
        weight_str = request.form.get("weight", "").strip()
        order_str = request.form.get("order", "0").strip()

        # Validate required fields
        if not name:
            flash("Komponentenname ist erforderlich.", "error")
            return redirect(url_for("exam.show", exam_id=exam_id))

        if not max_points_str:
            flash("Maximalpunkte sind erforderlich.", "error")
            return redirect(url_for("exam.show", exam_id=exam_id))

        if not weight_str:
            flash("Gewichtung ist erforderlich.", "error")
            return redirect(url_for("exam.show", exam_id=exam_id))

        # Parse numeric fields
        try:
            max_points = float(max_points_str)
        except ValueError:
            flash("Ungültiger Wert für Maximalpunkte.", "error")
            return redirect(url_for("exam.show", exam_id=exam_id))

        try:
            weight = float(weight_str)
        except ValueError:
            flash("Ungültiger Wert für Gewichtung.", "error")
            return redirect(url_for("exam.show", exam_id=exam_id))

        try:
            order = int(order_str)
        except ValueError:
            flash("Ungültiger Wert für Reihenfolge.", "error")
            return redirect(url_for("exam.show", exam_id=exam_id))

        # Use CLI function to add component (includes validation)
        component = add_component(
            name=name,
            max_points=max_points,
            weight=weight,
            exam_id=exam_id,
            description=description,
            order=order,
        )

        if component:
            flash(f"Komponente '{component.name}' erfolgreich hinzugefügt.", "success")
        else:
            flash("Fehler beim Hinzufügen der Komponente.", "error")

        return redirect(url_for("exam.show", exam_id=exam_id))

    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("exam.show", exam_id=exam_id))
    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while adding component: {e}")
        flash(
            "Fehler beim Hinzufügen der Komponente. Bitte versuchen Sie es erneut.",
            "error",
        )
        return redirect(url_for("exam.show", exam_id=exam_id))


@bp.route("/components/<int:component_id>/update", methods=["POST"])
def update_exam_component(component_id: int) -> Any:
    """
    Update an existing exam component.

    Args:
        component_id: Component database ID

    Form fields:
        name: Component name (optional)
        description: Component description (optional)
        max_points: Maximum points (optional)
        weight: Weight in exam grade (optional)
        order: Display order (optional)

    Returns:
        Redirect to exam detail page
    """
    try:
        # Get component to find exam_id for redirect
        component_obj = (
            app_module.db_session.query(ExamComponent)  # type: ignore[union-attr]
            .filter_by(id=component_id)
            .first()
        )

        if not component_obj:
            flash(f"Komponente mit ID {component_id} nicht gefunden.", "error")
            return redirect(url_for("exam.index"))

        exam_id = int(component_obj.exam_id)

        # Get form data
        name = request.form.get("name", "").strip() or None
        description = request.form.get("description", "").strip() or None
        max_points_str = request.form.get("max_points", "").strip()
        weight_str = request.form.get("weight", "").strip()
        order_str = request.form.get("order", "").strip()

        # Parse numeric fields if provided
        max_points = None
        if max_points_str:
            try:
                max_points = float(max_points_str)
            except ValueError:
                flash("Ungültiger Wert für Maximalpunkte.", "error")
                return redirect(url_for("exam.show", exam_id=exam_id))

        weight = None
        if weight_str:
            try:
                weight = float(weight_str)
            except ValueError:
                flash("Ungültiger Wert für Gewichtung.", "error")
                return redirect(url_for("exam.show", exam_id=exam_id))

        order = None
        if order_str:
            try:
                order = int(order_str)
            except ValueError:
                flash("Ungültiger Wert für Reihenfolge.", "error")
                return redirect(url_for("exam.show", exam_id=exam_id))

        # Use CLI function to update component (includes validation)
        component = update_component(
            component_id=component_id,
            name=name,
            description=description,
            max_points=max_points,
            weight=weight,
            order=order,
        )

        if component:
            flash(f"Komponente '{component.name}' erfolgreich aktualisiert.", "success")
        else:
            flash("Fehler beim Aktualisieren der Komponente.", "error")

        return redirect(url_for("exam.show", exam_id=exam_id))

    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("exam.show", exam_id=exam_id))
    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating component: {e}")
        flash(
            "Fehler beim Aktualisieren der Komponente. Bitte versuchen Sie es erneut.",
            "error",
        )
        return redirect(url_for("exam.show", exam_id=exam_id))


@bp.route("/components/<int:component_id>/delete", methods=["POST"])
def delete_exam_component(component_id: int) -> Any:
    """
    Delete an exam component.

    Args:
        component_id: Component database ID

    Returns:
        Redirect to exam detail page
    """
    try:
        # Get component to find exam_id for redirect
        component_obj = (
            app_module.db_session.query(ExamComponent)  # type: ignore[union-attr]
            .filter_by(id=component_id)
            .first()
        )

        if not component_obj:
            flash(f"Komponente mit ID {component_id} nicht gefunden.", "error")
            return redirect(url_for("exam.index"))

        exam_id = int(component_obj.exam_id)
        component_name = component_obj.name

        # Use CLI function to delete component
        if delete_component_cli(component_id):
            flash(f"Komponente '{component_name}' erfolgreich gelöscht.", "success")
        else:
            flash("Fehler beim Löschen der Komponente.", "error")

        return redirect(url_for("exam.show", exam_id=exam_id))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting component: {e}")
        flash(
            "Fehler beim Löschen der Komponente. Bitte versuchen Sie es erneut.",
            "error",
        )
        return redirect(url_for("exam.index"))
