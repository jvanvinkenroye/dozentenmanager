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
        "First Name",
        validators=[
            DataRequired(message="First name is required."),
            Length(max=100, message="First name cannot exceed 100 characters."),
        ],
    )

    last_name = StringField(
        "Last Name",
        validators=[
            DataRequired(message="Last name is required."),
            Length(max=100, message="Last name cannot exceed 100 characters."),
        ],
    )

    student_id = StringField(
        "Student ID",
        validators=[
            DataRequired(message="Student ID is required."),
            Regexp(
                r"^\d{8}$",
                message="Invalid student ID format. Must be exactly 8 digits.",
            ),
        ],
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Invalid email format."),
            Length(max=255, message="Email cannot exceed 255 characters."),
        ],
    )

    program = StringField(
        "Program",
        validators=[
            DataRequired(message="Program is required."),
            Length(max=200, message="Program cannot exceed 200 characters."),
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
            raise ValidationError("Student ID already exists.")

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
            raise ValidationError("Email address already exists.")
