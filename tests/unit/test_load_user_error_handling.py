"""
Unit tests for load_user error handling.

Verifies that Flask-Login's load_user callback handles malformed
user_id values gracefully (returns None instead of crashing).
"""

import pytest

from app import db, login_manager


@pytest.fixture
def user_in_db(app):
    """Create a test user in the database."""
    from app.models.user import User

    user = User(username="testload", email="load@test.com", role="admin")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user


def _get_load_user_callback(app):
    """Get the registered load_user callback from Flask-Login."""
    # Flask-Login stores the callback in login_manager.user_callback
    return login_manager.user_callback


class TestLoadUserErrorHandling:
    """Test that load_user handles malformed input gracefully."""

    def test_load_user_with_valid_id(self, app, user_in_db):
        """Valid user_id string should return the user."""
        callback = _get_load_user_callback(app)
        result = callback(str(user_in_db.id))
        assert result is not None
        assert result.username == "testload"

    def test_load_user_with_invalid_string(self, app):
        """Malformed user_id (non-numeric) should return None, not crash."""
        callback = _get_load_user_callback(app)
        result = callback("not-a-number")
        assert result is None

    def test_load_user_with_empty_string(self, app):
        """Empty user_id should return None, not crash."""
        callback = _get_load_user_callback(app)
        result = callback("")
        assert result is None

    def test_load_user_with_none(self, app):
        """None user_id should return None, not crash."""
        callback = _get_load_user_callback(app)
        result = callback(None)  # type: ignore[arg-type]
        assert result is None
