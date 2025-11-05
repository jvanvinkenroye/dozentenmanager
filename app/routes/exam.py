"""
Exam routes blueprint.

This module provides web routes for managing exams and exam components through the Flask interface.
"""

import logging
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import app as app_module
from cli.exam_cli import (
    add_exam,
    add_exam_component,
    delete_exam,
    delete_exam_component,
    list_exam_components,
    list_exams,
    show_exam,
    update_exam,
    update_exam_component,
    validate_exam_component_weights,
)
from app.models.course import Course

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
    course_id_str = request.args.get("course_id", "").strip()
    course_id = None

    if course_id_str:
        try:
            course_id = int(course_id_str)
        except ValueError:
            flash("Invalid course ID.", "error")

    try:
        exams = list_exams(course_id=course_id)

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
            course_id=course_id,
        )

    except (SQLAlchemyError, ValueError) as e:
        logger.error(f"Error while listing exams: {e}")
        flash("Error loading exams. Please try again.", "error")
        return render_template(
            "exam/list.html",
            exams=[],
            courses=[],
            course_id=None,
        )


@bp.route("/<int:exam_id>")
def show(exam_id: int) -> str | Any:
    """
    Show details for a specific exam, including its components.

    Args:
        exam_id: Exam database ID

    Returns:
        Rendered template with exam details or redirect
    """
    try:
        exam = show_exam(exam_id)

        if not exam:
            flash(f"Exam with ID {exam_id} not found.", "error")
            return redirect(url_for("exam.index"))

        # Get exam components
        components = list_exam_components(exam_id)

        # Validate component weights if components exist
        weights_valid = True
        total_weight = 0.0
        if components:
            weights_valid, total_weight = validate_exam_component_weights(exam_id)

        return render_template(
            "exam/detail.html",
            exam=exam,
            components=components,
            weights_valid=weights_valid,
            total_weight=total_weight,
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
        course_id: Course ID (required)
        name: Exam name (required)
        max_points: Maximum points (required)
        weight: Weight in final grade (required, 0-1)
        due_date: Due date (optional, YYYY-MM-DD format)

    Returns:
        Rendered template or redirect
    """
    if request.method == "GET":
        # Get all courses for dropdown
        try:
            courses = (
                app_module.db_session.query(Course)  # type: ignore[union-attr]
                .order_by(Course.semester.desc(), Course.name)
                .all()
            )
            return render_template("exam/form.html", exam=None, courses=courses)
        except SQLAlchemyError as e:
            logger.error(f"Database error while loading form: {e}")
            flash("Error loading form. Please try again.", "error")
            return redirect(url_for("exam.index"))

    # POST request - create exam
    try:
        course_id = int(request.form["course_id"])
        name = request.form["name"].strip()
        max_points = float(request.form["max_points"])
        weight = float(request.form["weight"])
        due_date = request.form.get("due_date", "").strip() or None

        exam = add_exam(
            course_id=course_id,
            name=name,
            max_points=max_points,
            weight=weight,
            due_date=due_date,
        )

        if exam:
            flash(f"Exam '{exam.name}' created successfully.", "success")
            return redirect(url_for("exam.show", exam_id=exam.id))
        else:
            flash("Failed to create exam. Please try again.", "error")
            return redirect(url_for("exam.new"))

    except KeyError as e:
        flash(f"Missing required field: {e}", "error")
        return redirect(url_for("exam.new"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("exam.new"))
    except Exception as e:
        logger.error(f"Error creating exam: {e}")
        flash("Error creating exam. Please try again.", "error")
        return redirect(url_for("exam.new"))


@bp.route("/<int:exam_id>/edit", methods=["GET", "POST"])
def edit(exam_id: int) -> str | Any:
    """
    Edit an existing exam.

    GET: Show form with current values
    POST: Update exam and redirect to detail page

    Args:
        exam_id: Exam database ID

    Form fields:
        name: Exam name (optional)
        max_points: Maximum points (optional)
        weight: Weight in final grade (optional, 0-1)
        due_date: Due date (optional, YYYY-MM-DD format)

    Returns:
        Rendered template or redirect
    """
    exam = show_exam(exam_id)
    if not exam:
        flash(f"Exam with ID {exam_id} not found.", "error")
        return redirect(url_for("exam.index"))

    if request.method == "GET":
        # Show edit form
        try:
            courses = (
                app_module.db_session.query(Course)  # type: ignore[union-attr]
                .order_by(Course.semester.desc(), Course.name)
                .all()
            )
            return render_template("exam/form.html", exam=exam, courses=courses)
        except SQLAlchemyError as e:
            logger.error(f"Database error while loading form: {e}")
            flash("Error loading form. Please try again.", "error")
            return redirect(url_for("exam.show", exam_id=exam_id))

    # POST request - update exam
    try:
        name = request.form.get("name", "").strip() or None
        max_points_str = request.form.get("max_points", "").strip()
        weight_str = request.form.get("weight", "").strip()
        due_date = request.form.get("due_date", "").strip() or None

        max_points = float(max_points_str) if max_points_str else None
        weight = float(weight_str) if weight_str else None

        exam = update_exam(
            exam_id=exam_id,
            name=name,
            max_points=max_points,
            weight=weight,
            due_date=due_date,
        )

        if exam:
            flash(f"Exam '{exam.name}' updated successfully.", "success")
            return redirect(url_for("exam.show", exam_id=exam.id))
        else:
            flash("Failed to update exam. Please try again.", "error")
            return redirect(url_for("exam.edit", exam_id=exam_id))

    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("exam.edit", exam_id=exam_id))
    except Exception as e:
        logger.error(f"Error updating exam: {e}")
        flash("Error updating exam. Please try again.", "error")
        return redirect(url_for("exam.edit", exam_id=exam_id))


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
        if delete_exam(exam_id):
            flash("Exam deleted successfully.", "success")
        else:
            flash("Failed to delete exam. Please try again.", "error")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        logger.error(f"Error deleting exam: {e}")
        flash("Error deleting exam. Please try again.", "error")

    return redirect(url_for("exam.index"))


# ============================================================================
# Exam Component Routes
# ============================================================================


@bp.route("/<int:exam_id>/components/new", methods=["GET", "POST"])
def new_component(exam_id: int) -> str | Any:
    """
    Create a new exam component.

    GET: Show form
    POST: Create component and redirect to exam detail page

    Args:
        exam_id: Exam database ID

    Form fields:
        name: Component name (required)
        max_points: Maximum points (required)
        weight: Weight within exam (required, 0-1)
        order: Display order (required)

    Returns:
        Rendered template or redirect
    """
    exam = show_exam(exam_id)
    if not exam:
        flash(f"Exam with ID {exam_id} not found.", "error")
        return redirect(url_for("exam.index"))

    if request.method == "GET":
        # Get next order number
        components = list_exam_components(exam_id)
        next_order = len(components) + 1

        return render_template(
            "exam/component_form.html",
            exam=exam,
            component=None,
            next_order=next_order,
        )

    # POST request - create component
    try:
        name = request.form["name"].strip()
        max_points = float(request.form["max_points"])
        weight = float(request.form["weight"])
        order = int(request.form["order"])

        component = add_exam_component(
            exam_id=exam_id,
            name=name,
            max_points=max_points,
            weight=weight,
            order=order,
        )

        if component:
            flash(f"Component '{component.name}' created successfully.", "success")
            return redirect(url_for("exam.show", exam_id=exam_id))
        else:
            flash("Failed to create component. Please try again.", "error")
            return redirect(url_for("exam.new_component", exam_id=exam_id))

    except KeyError as e:
        flash(f"Missing required field: {e}", "error")
        return redirect(url_for("exam.new_component", exam_id=exam_id))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("exam.new_component", exam_id=exam_id))
    except IntegrityError as e:
        flash(str(e), "error")
        return redirect(url_for("exam.new_component", exam_id=exam_id))
    except Exception as e:
        logger.error(f"Error creating component: {e}")
        flash("Error creating component. Please try again.", "error")
        return redirect(url_for("exam.new_component", exam_id=exam_id))


@bp.route("/<int:exam_id>/components/<int:component_id>/edit", methods=["GET", "POST"])
def edit_component(exam_id: int, component_id: int) -> str | Any:
    """
    Edit an existing exam component.

    GET: Show form with current values
    POST: Update component and redirect to exam detail page

    Args:
        exam_id: Exam database ID
        component_id: Component database ID

    Form fields:
        name: Component name (optional)
        max_points: Maximum points (optional)
        weight: Weight within exam (optional, 0-1)
        order: Display order (optional)

    Returns:
        Rendered template or redirect
    """
    exam = show_exam(exam_id)
    if not exam:
        flash(f"Exam with ID {exam_id} not found.", "error")
        return redirect(url_for("exam.index"))

    # Find the component
    components = list_exam_components(exam_id)
    component = None
    for comp in components:
        if comp.id == component_id:
            component = comp
            break

    if not component:
        flash(f"Component with ID {component_id} not found.", "error")
        return redirect(url_for("exam.show", exam_id=exam_id))

    if request.method == "GET":
        return render_template(
            "exam/component_form.html",
            exam=exam,
            component=component,
            next_order=None,
        )

    # POST request - update component
    try:
        name = request.form.get("name", "").strip() or None
        max_points_str = request.form.get("max_points", "").strip()
        weight_str = request.form.get("weight", "").strip()
        order_str = request.form.get("order", "").strip()

        max_points = float(max_points_str) if max_points_str else None
        weight = float(weight_str) if weight_str else None
        order = int(order_str) if order_str else None

        component = update_exam_component(
            component_id=component_id,
            name=name,
            max_points=max_points,
            weight=weight,
            order=order,
        )

        if component:
            flash(f"Component '{component.name}' updated successfully.", "success")
            return redirect(url_for("exam.show", exam_id=exam_id))
        else:
            flash("Failed to update component. Please try again.", "error")
            return redirect(
                url_for("exam.edit_component", exam_id=exam_id, component_id=component_id)
            )

    except ValueError as e:
        flash(str(e), "error")
        return redirect(
            url_for("exam.edit_component", exam_id=exam_id, component_id=component_id)
        )
    except Exception as e:
        logger.error(f"Error updating component: {e}")
        flash("Error updating component. Please try again.", "error")
        return redirect(
            url_for("exam.edit_component", exam_id=exam_id, component_id=component_id)
        )


@bp.route("/<int:exam_id>/components/<int:component_id>/delete", methods=["POST"])
def delete_component(exam_id: int, component_id: int) -> Any:
    """
    Delete an exam component.

    Args:
        exam_id: Exam database ID
        component_id: Component database ID

    Returns:
        Redirect to exam detail page
    """
    try:
        if delete_exam_component(component_id):
            flash("Component deleted successfully.", "success")
        else:
            flash("Failed to delete component. Please try again.", "error")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        logger.error(f"Error deleting component: {e}")
        flash("Error deleting component. Please try again.", "error")

    return redirect(url_for("exam.show", exam_id=exam_id))
