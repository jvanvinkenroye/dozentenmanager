"""
Pytest configuration and fixtures for Dozentenmanager tests.

This module provides common test fixtures for unit and integration tests.
"""

import pytest
from app import create_app
from app import db as _db


@pytest.fixture(scope="function")
def app():
    """
    Create application instance for testing.

    Yields:
        Flask application configured for testing
    """
    test_app = create_app("testing")

    with test_app.app_context():
        # Create all tables
        _db.create_all()

        yield test_app

        # Drop all tables after test
        _db.drop_all()
        _db.session.remove()


@pytest.fixture(scope="function")
def client(app):
    """
    Create test client for making requests.

    Args:
        app: Flask application fixture

    Returns:
        Flask test client
    """
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """
    Create CLI test runner.

    Args:
        app: Flask application fixture

    Returns:
        Flask CLI test runner
    """
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def db(app):
    """
    Provide database instance for tests.

    Args:
        app: Flask application fixture

    Returns:
        Flask-SQLAlchemy database instance
    """
    return _db
