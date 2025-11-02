"""
Configuration management for Dozentenmanager.

This module provides configuration classes for different environments:
- Development
- Testing
- Production
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration class with common settings."""

    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # SQLAlchemy configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Upload configuration
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "uploads"
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
    )  # 16MB default
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = "logs/dozentenmanager.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR}/dev_dozentenmanager.db"
    )
    SQLALCHEMY_ECHO = True  # Log SQL queries in development


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = False
    TESTING = True
    # Use in-memory SQLite database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Disable CSRF protection in tests
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR}/dozentenmanager.db"
    )

    # Ensure secret key is set in production
    SECRET_KEY = os.environ.get("SECRET_KEY") or Config.SECRET_KEY

    def __init__(self) -> None:
        """Validate production configuration."""
        if not os.environ.get("SECRET_KEY"):
            raise ValueError("SECRET_KEY must be set in production environment")


# Configuration dictionary for easy access
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name: Optional[str] = None) -> type[Config]:
    """
    Get configuration class for the specified environment.

    Args:
        config_name: Name of the configuration (development, testing, production)
                    If None, uses FLASK_ENV environment variable or 'default'

    Returns:
        Configuration class for the specified environment
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    return config.get(config_name, config["default"])
