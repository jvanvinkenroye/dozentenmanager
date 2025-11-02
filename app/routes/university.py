"""
University routes blueprint.

This module provides web routes for managing universities through the Flask interface.
"""

import logging
from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

import app as app_module
from app.models.university import University
from cli.university_cli import add_university, generate_slug, validate_slug

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("university", __name__, url_prefix="/universities")


@bp.route("/")
def index() -> str:
    """
    List all universities with optional search.

    Query parameters:
        search: Optional search term to filter by name or slug

    Returns:
        Rendered template with list of universities
    """
    search_term = request.args.get("search", "").strip()

    try:
        query = app_module.db_session.query(University)  # type: ignore[union-attr]

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                (University.name.ilike(search_pattern))
                | (University.slug.ilike(search_pattern))
            )

        universities = query.order_by(University.name).all()

        return render_template(
            "university/list.html",
            universities=universities,
            search_term=search_term,
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing universities: {e}")
        flash("Error loading universities. Please try again.", "error")
        return render_template("university/list.html", universities=[], search_term="")


@bp.route("/<int:university_id>")
def show(university_id: int) -> str | Any:
    """
    Show details for a specific university.

    Args:
        university_id: University ID

    Returns:
        Rendered template with university details or 404
    """
    try:
        university = (
            app_module.db_session.query(University)  # type: ignore[union-attr]
            .filter_by(id=university_id)
            .first()
        )

        if not university:
            flash(f"University with ID {university_id} not found.", "error")
            return redirect(url_for("university.index"))

        return render_template("university/detail.html", university=university)

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching university: {e}")
        flash("Error loading university details. Please try again.", "error")
        return redirect(url_for("university.index"))


@bp.route("/new", methods=["GET", "POST"])
def new() -> str | Any:
    """
    Create a new university.

    GET: Show form
    POST: Create university and redirect to detail page

    Form fields:
        name: University name (required)
        slug: URL-friendly identifier (optional, auto-generated if empty)

    Returns:
        Rendered form template (GET) or redirect to detail page (POST)
    """
    if request.method == "GET":
        return render_template("university/form.html", university=None)

    # POST: Create university
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip()

    # Validate name
    if not name:
        flash("University name is required.", "error")
        return render_template(
            "university/form.html", university=None, form_data=request.form
        )

    # Use slug if provided, otherwise generate
    if not slug:
        slug = generate_slug(name)
        logger.info(f"Auto-generated slug: {slug}")
    elif not validate_slug(slug):
        flash(
            "Invalid slug format. Slug must contain only lowercase letters, numbers, and hyphens.",
            "error",
        )
        return render_template(
            "university/form.html", university=None, form_data=request.form
        )

    try:
        university = add_university(name, slug)
        assert (
            university is not None
        )  # add_university returns University or raises exception
        flash(f"University '{university.name}' created successfully.", "success")
        return redirect(url_for("university.show", university_id=university.id))

    except ValueError as e:
        flash(str(e), "error")
        return render_template(
            "university/form.html", university=None, form_data=request.form
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error while creating university: {e}")
        flash("Error creating university. Please try again.", "error")
        return render_template(
            "university/form.html", university=None, form_data=request.form
        )


@bp.route("/<int:university_id>/edit", methods=["GET", "POST"])
def edit(university_id: int) -> str | Any:
    """
    Edit an existing university.

    GET: Show edit form
    POST: Update university and redirect to detail page

    Args:
        university_id: University ID

    Form fields:
        name: University name (required)
        slug: URL-friendly identifier (required)

    Returns:
        Rendered form template (GET) or redirect to detail page (POST)
    """
    try:
        university = (
            app_module.db_session.query(University)  # type: ignore[union-attr]
            .filter_by(id=university_id)
            .first()
        )

        if not university:
            flash(f"University with ID {university_id} not found.", "error")
            return redirect(url_for("university.index"))

        if request.method == "GET":
            return render_template("university/form.html", university=university)

        # POST: Update university
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip()

        # Validate inputs
        if not name:
            flash("University name is required.", "error")
            return render_template(
                "university/form.html", university=university, form_data=request.form
            )

        if not slug:
            flash("Slug is required.", "error")
            return render_template(
                "university/form.html", university=university, form_data=request.form
            )

        if not validate_slug(slug):
            flash(
                "Invalid slug format. Slug must contain only lowercase letters, numbers, and hyphens.",
                "error",
            )
            return render_template(
                "university/form.html", university=university, form_data=request.form
            )

        # Update fields
        university.name = name
        university.slug = slug

        app_module.db_session.commit()  # type: ignore[union-attr]
        flash(f"University '{university.name}' updated successfully.", "success")
        return redirect(url_for("university.show", university_id=university.id))

    except ValueError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        flash(str(e), "error")
        return render_template(
            "university/form.html", university=university, form_data=request.form
        )

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while updating university: {e}")
        flash("Error updating university. Please try again.", "error")
        return render_template(
            "university/form.html", university=university, form_data=request.form
        )


@bp.route("/<int:university_id>/delete", methods=["GET", "POST"])
def delete(university_id: int) -> str | Any:
    """
    Delete a university.

    GET: Show confirmation page
    POST: Delete university and redirect to list

    Args:
        university_id: University ID

    Returns:
        Rendered confirmation template (GET) or redirect to list (POST)
    """
    try:
        university = (
            app_module.db_session.query(University)  # type: ignore[union-attr]
            .filter_by(id=university_id)
            .first()
        )

        if not university:
            flash(f"University with ID {university_id} not found.", "error")
            return redirect(url_for("university.index"))

        if request.method == "GET":
            return render_template("university/delete.html", university=university)

        # POST: Delete university
        university_name = university.name
        app_module.db_session.delete(university)  # type: ignore[union-attr]
        app_module.db_session.commit()  # type: ignore[union-attr]

        flash(f"University '{university_name}' deleted successfully.", "success")
        return redirect(url_for("university.index"))

    except SQLAlchemyError as e:
        app_module.db_session.rollback()  # type: ignore[union-attr]
        logger.error(f"Database error while deleting university: {e}")
        flash("Error deleting university. Please try again.", "error")
        return redirect(url_for("university.show", university_id=university_id))
