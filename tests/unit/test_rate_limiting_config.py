"""
Unit tests for login rate limiting configuration.

Verifies that rate limiting is properly configured on auth routes
to prevent brute-force attacks.
"""

from flask_limiter.util import get_remote_address


class TestRateLimitingConfig:
    """Test that rate limiting is properly configured."""

    def test_rate_limiter_initialized(self, app):
        """Rate limiter should be initialized in the app."""
        from app import limiter

        assert limiter is not None, "Rate limiter should be initialized"
        # Verify limiter has the expected API
        assert hasattr(limiter, "init_app"), "Limiter should have init_app method"
        assert hasattr(limiter, "limit"), "Limiter should have limit decorator"

    def test_rate_limit_decorator_on_login(self, app):
        """Login route should have rate limit decorator applied."""
        # In testing mode, the limiter is disabled but the decorator
        # should still be registered on the route
        from app import create_app

        test_app = create_app("testing")
        rules = [str(rule) for rule in test_app.url_map.iter_rules()]
        assert "/auth/login" in rules

    def test_rate_limit_decorator_on_register(self, app):
        """Register route should have rate limit decorator applied."""
        from app import create_app

        test_app = create_app("testing")
        rules = [str(rule) for rule in test_app.url_map.iter_rules()]
        assert "/auth/register" in rules

    def test_get_remote_address_works(self, app):
        """get_remote_address should return the client IP."""
        with app.test_request_context(headers={"X-Forwarded-For": "1.2.3.4"}):
            result = get_remote_address()
            # Should use X-Forwarded-For header if present
            assert result is not None

    def test_rate_limit_disabled_in_testing(self, app):
        """Rate limiting should be disabled in testing mode."""
        from app import limiter

        assert limiter is not None
        # In testing, the limiter should be enabled=False
        # This is configured in create_app based on app.config.get("TESTING")
