"""
Document forms for web interface.

This module provides form validation for document upload and submission management.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    MultipleFileField,
    SelectField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional

from app.models.document import ALLOWED_EXTENSIONS
from app.models.submission import VALID_SUBMISSION_STATUSES


class DocumentUploadForm(FlaskForm):
    """Form for uploading a single document."""

    file = FileField(
        "Datei",
        validators=[
            FileRequired(message="Bitte wählen Sie eine Datei aus."),
            FileAllowed(
                list(ALLOWED_EXTENSIONS),
                message=f"Erlaubte Dateitypen: {', '.join(ALLOWED_EXTENSIONS)}",
            ),
        ],
    )

    enrollment_id = SelectField(
        "Einschreibung",
        coerce=int,
        validators=[DataRequired(message="Bitte wählen Sie eine Einschreibung aus.")],
    )

    submission_type = SelectField(
        "Typ",
        choices=[
            ("document", "Dokument"),
            ("assignment", "Hausarbeit"),
            ("exam_answer", "Prüfungsantwort"),
            ("email_attachment", "E-Mail-Anhang"),
        ],
        default="document",
        validators=[DataRequired()],
    )

    exam_id = SelectField(
        "Prüfung (optional)",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
    )

    notes = TextAreaField(
        "Notizen",
        validators=[
            Optional(),
            Length(max=1000, message="Notizen dürfen maximal 1000 Zeichen lang sein."),
        ],
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with empty choices."""
        super().__init__(*args, **kwargs)
        # Choices will be populated in the route
        self.enrollment_id.choices = []
        self.exam_id.choices = [("", "-- Keine Prüfung --")]


class BulkDocumentUploadForm(FlaskForm):
    """Form for uploading multiple documents at once."""

    files = MultipleFileField(
        "Dateien",
        validators=[
            DataRequired(message="Bitte wählen Sie mindestens eine Datei aus."),
        ],
    )

    course_id = SelectField(
        "Lehrveranstaltung",
        coerce=int,
        validators=[DataRequired(message="Bitte wählen Sie eine Lehrveranstaltung aus.")],
    )

    submission_type = SelectField(
        "Typ",
        choices=[
            ("document", "Dokument"),
            ("assignment", "Hausarbeit"),
            ("exam_answer", "Prüfungsantwort"),
        ],
        default="document",
        validators=[DataRequired()],
    )

    exam_id = SelectField(
        "Prüfung (optional)",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
    )

    notes = TextAreaField(
        "Notizen für alle Dokumente",
        validators=[
            Optional(),
            Length(max=1000, message="Notizen dürfen maximal 1000 Zeichen lang sein."),
        ],
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with empty choices."""
        super().__init__(*args, **kwargs)
        self.course_id.choices = []
        self.exam_id.choices = [("", "-- Keine Prüfung --")]


class SubmissionStatusForm(FlaskForm):
    """Form for updating submission status."""

    status = SelectField(
        "Status",
        choices=[
            ("submitted", "Eingereicht"),
            ("reviewed", "Überprüft"),
            ("graded", "Bewertet"),
            ("returned", "Zurückgegeben"),
        ],
        validators=[DataRequired(message="Bitte wählen Sie einen Status aus.")],
    )

    notes = TextAreaField(
        "Notizen",
        validators=[
            Optional(),
            Length(max=1000, message="Notizen dürfen maximal 1000 Zeichen lang sein."),
        ],
    )


class DocumentSearchForm(FlaskForm):
    """Form for searching documents."""

    class Meta:
        csrf = False  # Disable CSRF for search form (GET request)

    course_id = SelectField(
        "Lehrveranstaltung",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
    )

    student_id = SelectField(
        "Studierende/r",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
    )

    file_type = SelectField(
        "Dateityp",
        choices=[("", "-- Alle --")] + [(ext, ext.upper()) for ext in ALLOWED_EXTENSIONS],
        validators=[Optional()],
    )

    status = SelectField(
        "Status",
        choices=[("", "-- Alle --")]
        + [(s, s.capitalize()) for s in VALID_SUBMISSION_STATUSES],
        validators=[Optional()],
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with empty choices."""
        super().__init__(*args, **kwargs)
        self.course_id.choices = [("", "-- Alle Kurse --")]
        self.student_id.choices = [("", "-- Alle Studierende --")]
