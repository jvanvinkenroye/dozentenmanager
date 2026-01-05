"""
University form for web interface.

This module provides form validation for university creation and editing.
"""

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, ValidationError

from cli.university_cli import generate_slug
from app import db
from app.models.university import University


class UniversityForm(FlaskForm):
    """Form for creating and editing universities."""

    name = StringField(
        "Name",
        validators=[
            DataRequired(message="University name is required."),
            Length(max=255, message="University name cannot exceed 255 characters."),
        ],
    )

    slug = StringField(
        "Slug",
        validators=[
            Length(max=255, message="Slug cannot exceed 255 characters."),
        ],
    )

    def __init__(self, university=None, *args, **kwargs):
        """
        Initialize form.

        Args:
            university: Existing university instance (for edit forms)
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.university = university

    def validate_name(self, field):
        """
        Validate university name is unique.

        Args:
            field: WTForms field object

        Raises:
            ValidationError: If university name already exists
        """
        # Skip uniqueness check if editing the same university
        if self.university and field.data == self.university.name:
            return

        existing = db.session.query(University).filter_by(name=field.data).first()
        if existing:
            raise ValidationError("University with this name already exists.")

    def validate_slug(self, field):
        """
        Validate slug format and uniqueness.

        Args:
            field: WTForms field object

        Raises:
            ValidationError: If slug format is invalid or already exists
        """
        import re

        # Generate slug if not provided or empty
        if not field.data or not field.data.strip():
            field.data = generate_slug(self.name.data)
            return

        # Validate slug format if provided
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", field.data):
            raise ValidationError(
                "Invalid slug format. Slug must contain only lowercase letters, numbers, and hyphens."
            )

        # Skip uniqueness check if editing the same university
        if self.university and field.data == self.university.slug:
            return

        # Check for uniqueness
        existing = db.session.query(University).filter_by(slug=field.data).first()
        if existing:
            raise ValidationError("University with this slug already exists.")
