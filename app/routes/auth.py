"""
Authentication routes for Dozentenmanager.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from urllib.parse import urlsplit

from app import db
from app.forms.auth import LoginForm, RegistrationForm
from app.models.user import User
from app.services.audit_service import AuditService

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            # Log failed login attempt
            AuditService.log(
                action="login_failed",
                details={"username": form.username.data},
            )
            flash("Ungültiger Benutzername oder Passwort", "danger")
            return redirect(url_for("auth.login"))

        login_user(user, remember=form.remember_me.data)
        
        # Log successful login
        AuditService.log(
            action="login",
            user_id=user.id,
            details={"username": user.username},
        )
        
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)

    return render_template("auth/login.html", title="Anmelden", form=form)


@bp.route("/logout")
def logout():
    """Handle user logout."""
    if current_user.is_authenticated:
        user_id = current_user.id
        username = current_user.username
        logout_user()
        
        # Log logout
        AuditService.log(
            action="logout",
            user_id=user_id,
            details={"username": username},
        )
    else:
        logout_user()
        
    flash("Sie wurden erfolgreich abgemeldet.", "info")
    return redirect(url_for("index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            role="lecturer"  # Default role
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Log registration
        AuditService.log(
            action="register",
            user_id=user.id,
            details={"username": user.username, "email": user.email},
        )
        
        flash("Registrierung erfolgreich. Sie können sich nun anmelden.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("auth/register.html", title="Registrieren", form=form)
