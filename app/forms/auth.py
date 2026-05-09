"""
Authentication forms for Dozentenmanager.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

from app.models.user import User


class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField("Benutzername", validators=[DataRequired()])
    password = PasswordField("Passwort", validators=[DataRequired()])
    remember_me = BooleanField("Angemeldet bleiben")
    submit = SubmitField("Anmelden")


class RegistrationForm(FlaskForm):
    """Form for user registration."""
    username = StringField("Benutzername", validators=[DataRequired()])
    email = StringField("E-Mail", validators=[DataRequired(), Email()])
    password = PasswordField("Passwort", validators=[DataRequired()])
    password_confirm = PasswordField(
        "Passwort wiederholen", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Registrieren")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Dieser Benutzername ist bereits vergeben.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError("Diese E-Mail-Adresse wird bereits verwendet.")
