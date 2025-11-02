"""
Pytest configuration and fixtures for Dozentenmanager tests.

This module provides common test fixtures for unit and integration tests.
"""

import pytest
from app import create_app, Base, db_session


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
        Base.metadata.create_all(bind=db_session.get_bind())

        yield test_app

        # Drop all tables after test
        Base.metadata.drop_all(bind=db_session.get_bind())
        db_session.remove()


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
    return db_session
