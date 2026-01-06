"""
Email import forms for web interface.

This module provides form validation for email file import.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SelectField
from wtforms.validators import DataRequired, Optional


class EmailImportForm(FlaskForm):
    """Form for importing emails from .eml or .mbox files."""

    file = FileField(
        "E-Mail-Datei",
        validators=[
            FileRequired(message="Bitte wählen Sie eine Datei aus."),
            FileAllowed(
                ["eml", "mbox"],
                message="Erlaubte Dateitypen: .eml, .mbox",
            ),
        ],
    )

    course_id = SelectField(
        "Lehrveranstaltung (optional)",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with empty choices."""
        super().__init__(*args, **kwargs)
        self.course_id.choices = [("", "-- Alle Kurse --")]
