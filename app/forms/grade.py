"""
Flask-WTF forms for grading management.

This module defines forms for adding/updating grades and managing
exam components.
"""

from flask_wtf import FlaskForm
from wtforms import (
    FloatField,
    SelectField,
    TextAreaField,
    BooleanField,
    StringField,
    IntegerField,
    HiddenField,
)
from wtforms.validators import (
    DataRequired,
    NumberRange,
    Optional,
    Length,
    ValidationError,
)


class GradeForm(FlaskForm):
    """Form for adding/updating a grade."""

    enrollment_id = SelectField(
        "Student (Einschreibung)",
        coerce=int,
        validators=[DataRequired(message="Bitte wählen Sie einen Studenten")],
    )
    exam_id = SelectField(
        "Prüfung",
        coerce=int,
        validators=[DataRequired(message="Bitte wählen Sie eine Prüfung")],
    )
    component_id = SelectField(
        "Komponente (optional)",
        coerce=int,
        validators=[Optional()],
        choices=[(0, "--- Keine Komponente ---")],
    )
    points = FloatField(
        "Punkte",
        validators=[
            DataRequired(message="Bitte geben Sie die Punkte ein"),
            NumberRange(min=0, message="Punkte müssen >= 0 sein"),
        ],
    )
    graded_by = StringField(
        "Benotet von",
        validators=[Optional(), Length(max=100)],
    )
    is_final = BooleanField("Endnote")
    notes = TextAreaField(
        "Anmerkungen",
        validators=[Optional(), Length(max=1000)],
    )


class BulkGradeForm(FlaskForm):
    """Form for bulk grading multiple students."""

    exam_id = SelectField(
        "Prüfung",
        coerce=int,
        validators=[DataRequired(message="Bitte wählen Sie eine Prüfung")],
    )
    component_id = SelectField(
        "Komponente (optional)",
        coerce=int,
        validators=[Optional()],
        choices=[(0, "--- Keine Komponente ---")],
    )
    graded_by = StringField(
        "Benotet von",
        validators=[Optional(), Length(max=100)],
    )
    is_final = BooleanField("Als Endnote markieren")


class ExamComponentForm(FlaskForm):
    """Form for adding/updating exam components."""

    exam_id = HiddenField()
    name = StringField(
        "Komponentenname",
        validators=[
            DataRequired(message="Bitte geben Sie einen Namen ein"),
            Length(max=255, message="Name darf maximal 255 Zeichen haben"),
        ],
    )
    weight = FloatField(
        "Gewichtung (%)",
        validators=[
            DataRequired(message="Bitte geben Sie die Gewichtung ein"),
            NumberRange(
                min=0.1,
                max=100,
                message="Gewichtung muss zwischen 0.1 und 100 liegen",
            ),
        ],
    )
    max_points = FloatField(
        "Maximale Punkte",
        validators=[
            DataRequired(message="Bitte geben Sie die maximalen Punkte ein"),
            NumberRange(min=0.1, message="Maximale Punkte müssen > 0 sein"),
        ],
    )
    order = IntegerField(
        "Reihenfolge",
        validators=[Optional()],
        default=0,
    )
    description = TextAreaField(
        "Beschreibung",
        validators=[Optional(), Length(max=500)],
    )


class GradeFilterForm(FlaskForm):
    """Form for filtering grades."""

    course_id = SelectField(
        "Kurs",
        coerce=int,
        validators=[Optional()],
        choices=[(0, "Alle Kurse")],
    )
    exam_id = SelectField(
        "Prüfung",
        coerce=int,
        validators=[Optional()],
        choices=[(0, "Alle Prüfungen")],
    )
    student_id = SelectField(
        "Student",
        coerce=int,
        validators=[Optional()],
        choices=[(0, "Alle Studenten")],
    )
    is_final = SelectField(
        "Status",
        choices=[
            ("", "Alle"),
            ("1", "Nur Endnoten"),
            ("0", "Nur vorläufige Noten"),
        ],
        validators=[Optional()],
    )


class GradeSearchForm(FlaskForm):
    """Form for searching grades."""

    query = StringField(
        "Suche",
        validators=[Optional(), Length(max=100)],
    )
    min_grade = FloatField(
        "Min. Note",
        validators=[Optional(), NumberRange(min=1.0, max=5.0)],
    )
    max_grade = FloatField(
        "Max. Note",
        validators=[Optional(), NumberRange(min=1.0, max=5.0)],
    )
