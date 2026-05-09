"""
Course form for web interface.

This module provides form validation for course creation and editing.
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError

from app import db
from app.models.course import Course, generate_slug


class CourseForm(FlaskForm):
    """Form for creating and editing courses."""

    name = StringField(
        "Name",
        validators=[
            DataRequired(message="Course name is required."),
            Length(max=255, message="Course name cannot exceed 255 characters."),
        ],
    )

    semester = StringField(
        "Semester",
        validators=[
            DataRequired(message="Semester is required."),
            Regexp(
                r"^\d{4}_(SoSe|WiSe)$",
                message="Invalid semester format. Must be YYYY_SoSe or YYYY_WiSe (e.g., 2023_SoSe, 2024_WiSe)",
            ),
        ],
    )

    university_id = SelectField(
        "University",
        coerce=int,
        validators=[DataRequired(message="University is required.")],
    )

    slug = StringField(
        "Slug",
        validators=[
            Optional(),
            Length(max=255, message="Slug cannot exceed 255 characters."),
        ],
    )

    def __init__(self, course=None, *args, **kwargs):
        """
        Initialize form.

        Args:
            course: Existing course instance (for edit forms)
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.course = course

    def validate_slug(self, field):
        """
        Validate slug is unique within semester and university.

        Args:
            field: WTForms field object

        Raises:
            ValidationError: If slug already exists in the same semester
        """
        # Generate slug if not provided or empty
        if not field.data or not field.data.strip():
            field.data = generate_slug(self.name.data or "")
            return

        # Skip uniqueness check if editing the same course
        if (
            self.course
            and field.data == self.course.slug
            and self.semester.data == self.course.semester
        ):
            return

        # Check for duplicate slug in same semester and university
        existing = (
            db.session.query(Course)
            .filter_by(
                slug=field.data,
                semester=self.semester.data,
                university_id=self.university_id.data,
            )
            .first()
        )
        if existing:
            raise ValidationError(
                "A course with this slug already exists in this semester and university."
            )
