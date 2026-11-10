"""Import forms for CSV/XLSX/XLS import of courses, enrollments, and grades."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import SelectField
from wtforms.validators import DataRequired

FORMAT_CHOICES = [
    ("", "Automatisch"),
    ("csv", "CSV"),
    ("xlsx", "Excel (.xlsx)"),
    ("xls", "Excel (.xls)"),
]

DUPLICATE_CHOICES = [
    ("skip", "Überspringen"),
    ("update", "Aktualisieren"),
    ("error", "Fehler"),
]

FILE_VALIDATORS = [
    FileRequired(message="Bitte eine Datei auswählen."),
    FileAllowed(
        ["csv", "xlsx", "xls"], message="Nur CSV, XLSX oder XLS Dateien sind erlaubt."
    ),
]


class CourseImportForm(FlaskForm):
    """Form for importing courses from CSV/XLSX/XLS."""

    file = FileField("Datei", validators=FILE_VALIDATORS)
    file_format = SelectField("Format (optional)", choices=FORMAT_CHOICES)
    university_id = SelectField("Hochschule", coerce=int, validators=[DataRequired()])
    on_duplicate = SelectField("Duplikate", choices=DUPLICATE_CHOICES, default="skip")


class EnrollmentImportForm(FlaskForm):
    """Form for importing enrollments from CSV/XLSX/XLS."""

    file = FileField("Datei", validators=FILE_VALIDATORS)
    file_format = SelectField("Format (optional)", choices=FORMAT_CHOICES)


class GradeImportForm(FlaskForm):
    """Form for importing grades from CSV/XLSX/XLS."""

    file = FileField("Datei", validators=FILE_VALIDATORS)
    file_format = SelectField("Format (optional)", choices=FORMAT_CHOICES)
    on_duplicate = SelectField("Duplikate", choices=DUPLICATE_CHOICES, default="skip")
