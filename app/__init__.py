"""
Flask application factory for Dozentenmanager.

This module creates and configures the Flask application instance using
the application factory pattern for better testability and flexibility.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import get_config

# Create Flask-SQLAlchemy instance
db = SQLAlchemy()

# CSRF Protection
csrf = CSRFProtect()


def create_app(config_name: str | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: Name of configuration to use (development, testing, production)
                    If None, uses FLASK_ENV environment variable or 'development'

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app.config.from_object(get_config(config_name))

    # Initialize CSRF protection
    csrf.init_app(app)

    # Initialize database
    init_db(app)

    # Setup logging
    setup_logging(app)

    # Register blueprints
    register_blueprints(app)

    # Create upload directory if it doesn't exist
    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)

    # Register error handlers
    register_error_handlers(app)

    # Add context processors
    register_context_processors(app)

    app.logger.info(f"Dozentenmanager startup - Environment: {config_name}")

    return app


def init_db(app: Flask) -> None:
    """
    Initialize database connection and session.

    Args:
        app: Flask application instance
    """
    # Initialize Flask-SQLAlchemy
    db.init_app(app)

    # Import models here to avoid circular imports
    from app import models  # noqa: F401

    # Create tables if they don't exist (in development/testing)
    with app.app_context():
        if app.config["DEBUG"] or app.config["TESTING"]:
            db.create_all()


def setup_logging(app: Flask) -> None:
    """
    Configure application logging.

    Args:
        app: Flask application instance
    """
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # File handler with rotation
        file_handler = RotatingFileHandler(
            app.config["LOG_FILE"],
            maxBytes=app.config["LOG_MAX_BYTES"],
            backupCount=app.config["LOG_BACKUP_COUNT"],
        )

        # Set format
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )

        # Set level from config
        log_level = getattr(logging, app.config["LOG_LEVEL"].upper(), logging.INFO)
        file_handler.setLevel(log_level)

        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)

        app.logger.info("Dozentenmanager logging initialized")


def register_blueprints(app: Flask) -> None:
    """
    Register Flask blueprints for different routes.

    Args:
        app: Flask application instance
    """
    # Import blueprints here to avoid circular imports
    from app.routes.course import bp as course_bp
    from app.routes.document import bp as document_bp
    from app.routes.enrollment import bp as enrollment_bp
    from app.routes.exam import bp as exam_bp
    from app.routes.grade import bp as grade_bp
    from app.routes.student import bp as student_bp
    from app.routes.university import bp as university_bp

    # Register blueprints
    app.register_blueprint(course_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(enrollment_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(grade_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(university_bp)

    # Register index route
    @app.route("/")
    def index():
        """
        Render the home page with dashboard statistics.

        Returns:
            Rendered home template with statistics
        """
        from flask import render_template

        from app.models import Course, Enrollment, Student, University

        # Get statistics from database
        stats = {
            "universities": University.query.count(),
            "students": Student.query.count(),
            "courses": Course.query.count(),
            "enrollments": Enrollment.query.filter_by(status="active").count(),
        }

        return render_template("home.html", stats=stats)


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for common HTTP errors.

    Args:
        app: Flask application instance
    """
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        db.session.rollback()
        app.logger.error(f"Internal server error: {error}")
        return render_template("errors/500.html"), 500


def register_context_processors(app: Flask) -> None:
    """
    Register template context processors.

    Args:
        app: Flask application instance
    """

    @app.context_processor
    def utility_processor():
        """Make utility functions available in templates."""
        return {}
