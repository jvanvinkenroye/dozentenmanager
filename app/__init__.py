"""
Flask application factory for Dozentenmanager.

This module creates and configures the Flask application instance using
the application factory pattern for better testability and flexibility.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from config import get_config

# Create SQLAlchemy base for models
Base = declarative_base()

# Database session (will be initialized in create_app)
db_session = None


def create_app(config_name: Optional[str] = None) -> Flask:
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
    global db_session

    # Create database engine
    engine = create_engine(
        app.config["SQLALCHEMY_DATABASE_URI"], echo=app.config["SQLALCHEMY_ECHO"]
    )

    # Create scoped session
    db_session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    # Make session available to models
    Base.query = db_session.query_property()

    # Import models here to avoid circular imports
    from app import models  # noqa: F401

    # Create tables if they don't exist (in development/testing)
    if app.config["DEBUG"] or app.config["TESTING"]:
        Base.metadata.create_all(bind=engine)

    # Register teardown handler to close session
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()


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
    from app.routes.student import bp as student_bp
    from app.routes.university import bp as university_bp

    # Register blueprints
    app.register_blueprint(course_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(university_bp)

    # Temporary: Register a simple index route
    @app.route("/")
    def index():
        return """
        <html>
            <head><title>Dozentenmanager</title></head>
            <body>
                <h1>Dozentenmanager</h1>
                <p>Student Management System</p>
                <p>Application is running successfully!</p>
                <ul>
                    <li><a href="/students">Students</a></li>
                    <li><a href="/universities">Universities</a></li>
                </ul>
            </body>
        </html>
        """


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for common HTTP errors.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(404)
    def not_found_error(error):
        return (
            """
        <html>
            <head><title>404 - Not Found</title></head>
            <body>
                <h1>404 - Page Not Found</h1>
                <p>The page you are looking for does not exist.</p>
            </body>
        </html>
        """,
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        db_session.rollback()
        app.logger.error(f"Internal server error: {error}")
        return (
            """
        <html>
            <head><title>500 - Internal Server Error</title></head>
            <body>
                <h1>500 - Internal Server Error</h1>
                <p>An internal server error occurred.</p>
            </body>
        </html>
        """,
            500,
        )


def register_context_processors(app: Flask) -> None:
    """
    Register template context processors.

    Args:
        app: Flask application instance
    """

    @app.context_processor
    def utility_processor():
        """Make utility functions available in templates."""
        return dict()
