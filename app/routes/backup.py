"""
Backup routes blueprint.

This module provides web routes for creating and restoring backups through the Flask interface.
"""

import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from flask_login import login_required
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.utils import secure_filename

from app.utils.auth import admin_required
from cli.backup_cli import create_backup, restore_backup

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("backup", __name__, url_prefix="/backup")


@bp.route("/")
@login_required
@admin_required
def index() -> str:
    """
    Show backup management page.

    Returns:
        Rendered template for backup management
    """
    return render_template("backup/index.html")


@bp.route("/create", methods=["POST"])
@login_required
@admin_required
def create() -> Any:
    """
    Create a new backup and download it.

    Form parameters:
        include_uploads: Whether to include uploaded files (checkbox)

    Returns:
        File download response or redirect on error
    """
    try:
        include_uploads = request.form.get("include_uploads") == "on"

        logger.info(
            f"Creating backup (include_uploads={include_uploads}) via web interface"
        )

        # Create backup in temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            backup_filename = f"dozentenmanager_backup_{timestamp}"
            temp_file = str(Path(temp_dir) / backup_filename)

            # Create backup using CLI function
            backup_path = create_backup(temp_file, include_uploads=include_uploads)

            logger.info(f"Backup created successfully: {backup_path}")

            # Send file for download
            return send_file(  # type: ignore[call-arg]
                backup_path,
                as_attachment=True,
                download_name=backup_path.name,
                mimetype="application/zip",
            )

    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        flash(f"Error creating backup: {e}", "error")
        return redirect(url_for("backup.index"))


@bp.route("/restore", methods=["POST"])
@login_required
@admin_required
def restore() -> Any:
    """
    Restore data from an uploaded backup file.

    Form parameters:
        backup_file: Uploaded ZIP file containing backup
        clear_existing: Whether to clear existing data before restore (checkbox)

    Returns:
        Redirect to backup index with status message
    """
    try:
        # Check if file was uploaded
        if "backup_file" not in request.files:
            flash("No backup file provided", "error")
            return redirect(url_for("backup.index"))

        file = request.files["backup_file"]

        # Check if filename is empty
        if file.filename == "":
            flash("No backup file selected", "error")
            return redirect(url_for("backup.index"))

        # Check file extension
        if not file.filename or not file.filename.endswith(".zip"):
            flash("Invalid file format. Please upload a ZIP file.", "error")
            return redirect(url_for("backup.index"))

        clear_existing = request.form.get("clear_existing") == "on"

        logger.info(
            f"Restoring backup from {file.filename} (clear_existing={clear_existing})"
        )

        # Save uploaded file to temporary location
        filename = secure_filename(file.filename)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / filename
            file.save(temp_path)

            # Restore backup using CLI function
            restore_backup(str(temp_path), clear_existing=clear_existing)

        logger.info("Backup restored successfully")
        flash("Backup restored successfully!", "success")
        return redirect(url_for("backup.index"))

    except ValueError as e:
        logger.error(f"Invalid backup file: {e}")
        flash(f"Invalid backup file: {e}", "error")
        return redirect(url_for("backup.index"))

    except Exception as e:
        logger.error(f"Error restoring backup: {e}", exc_info=True)
        flash(f"Error restoring backup: {e}", "error")
        return redirect(url_for("backup.index"))
