"""
Student form for web interface.

This module provides form validation for student creation and editing.
"""

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Email, Length, Regexp, ValidationError

from app import db
from app.models.student import Student


class StudentForm(FlaskForm):
    """Form for creating and editing students."""

    first_name = StringField(
        "Vorname",
        validators=[
            DataRequired(message="Vorname ist erforderlich."),
            Length(max=100, message="Vorname darf maximal 100 Zeichen haben."),
        ],
    )

    last_name = StringField(
        "Nachname",
        validators=[
            DataRequired(message="Nachname ist erforderlich."),
            Length(max=100, message="Nachname darf maximal 100 Zeichen haben."),
        ],
    )

    student_id = StringField(
        "Matrikelnummer",
        validators=[
            DataRequired(message="Matrikelnummer ist erforderlich."),
            Regexp(
                r"^\d{8}$",
                message="Ungültiges Format. Die Matrikelnummer muss genau 8 Ziffern haben.",
            ),
        ],
    )

    email = StringField(
        "E-Mail",
        validators=[
            DataRequired(message="E-Mail ist erforderlich."),
            Email(message="Ungültiges E-Mail-Format."),
            Length(max=255, message="E-Mail darf maximal 255 Zeichen haben."),
        ],
    )

    program = StringField(
        "Studiengang",
        validators=[
            DataRequired(message="Studiengang ist erforderlich."),
            Length(max=200, message="Studiengang darf maximal 200 Zeichen haben."),
        ],
    )

    def __init__(self, student=None, *args, **kwargs):
        """
        Initialize form.

        Args:
            student: Existing student instance (for edit forms)
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.student = student

    def validate_student_id(self, field):
        """
        Validate student ID is unique.

        Args:
            field: WTForms field object

        Raises:
            ValidationError: If student ID already exists
        """
        # Skip uniqueness check if editing the same student
        if self.student and field.data == self.student.student_id:
            return

        existing = db.session.query(Student).filter_by(student_id=field.data).first()
        if existing:
            raise ValidationError("Matrikelnummer existiert bereits.")

    def validate_email(self, field):
        """
        Validate email is unique.

        Args:
            field: WTForms field object

        Raises:
            ValidationError: If email already exists
        """
        # Convert to lowercase for comparison
        email_lower = field.data.lower()

        # Skip uniqueness check if editing the same student
        if self.student and email_lower == self.student.email:
            return

        existing = db.session.query(Student).filter_by(email=email_lower).first()
        if existing:
            raise ValidationError("E-Mail-Adresse existiert bereits.")
