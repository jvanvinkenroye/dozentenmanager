"""Tests for session security configuration."""

import os
from unittest.mock import patch

from config import (
    Config,
    DevelopmentConfig,
    ProductionConfig,
)


class TestProductionSessionSecurity:
    """Test session security settings in ProductionConfig."""

    def test_session_cookie_secure_true(self):
        """SESSION_COOKIE_SECURE must be True in production."""
        config = ProductionConfig()
        assert config.SESSION_COOKIE_SECURE is True

    def test_session_cookie_http_only_true(self):
        """SESSION_COOKIE_HTTPONLY must be True to prevent JS access."""
        config = ProductionConfig()
        assert config.SESSION_COOKIE_HTTPONLY is True

    def test_session_cookie_samesite_set(self):
        """SESSION_COOKIE_SAMESITE must be set for CSRF protection."""
        config = ProductionConfig()
        assert config.SESSION_COOKIE_SAMESITE == "Lax"

    def test_permanent_session_lifetime(self):
        """PERMANENT_SESSION_LIFETIME should be 1 hour (3600s)."""
        config = ProductionConfig()
        assert config.PERMANENT_SESSION_LIFETIME == 3600

    def test_secret_key_not_default(self):
        """Test that SECRET_KEY is set (production __init__ enforces this)."""
        with patch.dict(
            os.environ,
            {"FLASK_SECRET_KEY": "test-secret-key-for-testing"},
        ):
            config = ProductionConfig()
            assert config.SECRET_KEY is not None
            assert config.SECRET_KEY != "dev-secret-key-change-in-production"  # noqa: S105

    def test_production_rejects_missing_secret_key(self):
        """Test that ProductionConfig raises ValueError without SECRET_KEY."""
        with patch.dict(os.environ, {"FLASK_SECRET_KEY": "", "SECRET_KEY": ""}):
            try:
                ProductionConfig()
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "SECRET_KEY" in str(e)


class TestDevelopmentSessionSecurity:
    """Test session security settings in DevelopmentConfig."""

    def test_session_cookie_secure_false_in_dev(self):
        """SESSION_COOKIE_SECURE must be False for local development."""
        config = DevelopmentConfig()
        assert config.SESSION_COOKIE_SECURE is False

    def test_other_session_settings_applied(self):
        """Other session settings should still apply in development."""
        config = DevelopmentConfig()
        assert config.SESSION_COOKIE_HTTPONLY is True
        assert config.SESSION_COOKIE_SAMESITE == "Lax"
        assert config.PERMANENT_SESSION_LIFETIME == 3600


class TestBaseConfigSessionSecurity:
    """Test that base Config defines all session security settings."""

    def test_base_config_has_all_settings(self):
        """Base Config must define all session security attributes."""
        assert hasattr(Config, "SESSION_COOKIE_SECURE")
        assert hasattr(Config, "SESSION_COOKIE_HTTPONLY")
        assert hasattr(Config, "SESSION_COOKIE_SAMESITE")
        assert hasattr(Config, "PERMANENT_SESSION_LIFETIME")

    def test_base_config_secure_defaults(self):
        """Base Config must use secure defaults."""
        assert Config.SESSION_COOKIE_SECURE is True
        assert Config.SESSION_COOKIE_HTTPONLY is True
        assert Config.SESSION_COOKIE_SAMESITE == "Lax"
        assert Config.PERMANENT_SESSION_LIFETIME == 3600

    def test_secret_key_set_in_base_config(self):
        """Base Config must have a SECRET_KEY set."""
        assert Config.SECRET_KEY is not None
        assert len(Config.SECRET_KEY) > 0

    def test_dev_config_secret_key_from_env(self):
        """Development SECRET_KEY comes from dotenv or env var at import time."""
        config = DevelopmentConfig()
        assert config.SECRET_KEY is not None
        assert len(config.SECRET_KEY) > 0
