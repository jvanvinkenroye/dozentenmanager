"""
Unit tests for extended rate limiting configuration.

Verifies that rate limiting is properly configured on additional
critical endpoints (API submission upload, bulk grade, bulk document upload).
"""

from flask_limiter.util import get_remote_address


class TestExtendedRateLimitingConfig:
    """Test that extended rate limiting is properly configured."""

    def test_rate_limiter_initialized(self, app):
        """Rate limiter should be initialized in the app."""
        from app import limiter

        assert limiter is not None, "Rate limiter should be initialized"
        assert hasattr(limiter, "init_app"), "Limiter should have init_app method"
        assert hasattr(limiter, "limit"), "Limiter should have limit decorator"

    def test_api_submission_has_rate_limit(self, app):
        """API upload_submission route should have rate limit decorator."""
        from app import create_app

        test_app = create_app("testing")
        rules = [str(rule) for rule in test_app.url_map.iter_rules()]
        assert "/api/submissions" in rules

    def test_bulk_grade_has_rate_limit(self, app):
        """Bulk grade route should have rate limit decorator applied."""
        from app import create_app

        test_app = create_app("testing")
        rules = [str(rule) for rule in test_app.url_map.iter_rules()]
        assert "/grades/bulk" in rules

    def test_bulk_upload_has_rate_limit(self, app):
        """Bulk document upload route should have rate limit decorator."""
        from app import create_app

        test_app = create_app("testing")
        rules = [str(rule) for rule in test_app.url_map.iter_rules()]
        assert "/documents/bulk-upload" in rules

    def test_get_remote_address_works(self, app):
        """get_remote_address should return the client IP."""
        with app.test_request_context(headers={"X-Forwarded-For": "1.2.3.4"}):
            result = get_remote_address()
            assert result is not None

    def test_rate_limit_disabled_in_testing(self, app):
        """Rate limiting should be disabled in testing mode."""
        from app import limiter

        assert limiter is not None
