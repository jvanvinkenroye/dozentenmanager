"""
Exam form for web interface.

This module provides form validation for exam creation and editing.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, FloatField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class ExamForm(FlaskForm):
    """Form for creating and editing exams."""

    name = StringField(
        "Name",
        validators=[
            DataRequired(message="Exam name is required."),
            Length(max=255, message="Exam name cannot exceed 255 characters."),
        ],
    )

    course_id = SelectField(
        "Course",
        coerce=int,
        validators=[DataRequired(message="Course is required.")],
    )

    exam_date = DateField(
        "Exam Date",
        format="%Y-%m-%d",
        validators=[DataRequired(message="Exam date is required.")],
    )

    max_points = FloatField(
        "Maximum Points",
        validators=[
            DataRequired(message="Maximum points is required."),
            NumberRange(min=0.01, message="Maximum points must be greater than 0."),
        ],
    )

    weight = FloatField(
        "Weight (%)",
        default=100.0,
        validators=[
            Optional(),
            NumberRange(
                min=0,
                max=100,
                message="Weight must be between 0 and 100%.",
            ),
        ],
    )

    description = TextAreaField(
        "Description",
        validators=[
            Optional(),
            Length(max=500, message="Description cannot exceed 500 characters."),
        ],
    )

    def __init__(self, exam=None, *args, **kwargs):
        """
        Initialize form.

        Args:
            exam: Existing exam instance (for edit forms)
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.exam = exam
