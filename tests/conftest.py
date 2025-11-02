"""
Pytest configuration and fixtures for Dozentenmanager tests.

This module provides common test fixtures for unit and integration tests.
"""

import pytest
import app as app_module
from app import create_app, Base


@pytest.fixture(scope="function")
def app():
    """
    Create application instance for testing.

    Yields:
        Flask application configured for testing
    """
    test_app = create_app("testing")

    with test_app.app_context():
        # Create all tables (db_session is initialized by create_app)
        Base.metadata.create_all(bind=app_module.db_session.get_bind())

        yield test_app

        # Drop all tables after test
        Base.metadata.drop_all(bind=app_module.db_session.get_bind())
        app_module.db_session.remove()


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
    Provide database session for tests.

    Args:
        app: Flask application fixture

    Returns:
        SQLAlchemy database session
    """
    return app_module.db_session
