"""
Unit tests for safe redirect utility.

This module tests the safe_redirect function that prevents open redirect attacks
by only allowing redirects to same-origin URLs.
"""

from app.utils.redirect import is_same_origin, safe_redirect


class TestIsSameOrigin:
    """Test is_same_origin helper function."""

    def test_relative_url_is_same_origin(self):
        """Relative URLs (no scheme/host) should be considered same-origin."""
        assert is_same_origin("/students") is True
        assert is_same_origin("/courses/1") is True
        assert is_same_origin("") is True

    def test_full_url_with_host_is_not_same_origin(self):
        """Full URLs with a host should NOT be considered same-origin (strict mode)."""
        assert is_same_origin("http://localhost:5000/students") is False

    def test_different_host_is_not_same_origin(self):
        """URLs with different hosts should NOT be same-origin."""
        assert is_same_origin("http://evil.com/steal") is False
        assert is_same_origin("https://phishing.example.net/") is False
        assert is_same_origin("http://attacker.com") is False
        assert is_same_origin("//evil.com/path") is False  # protocol-relative

    def test_javascript_url_is_blocked(self):
        """JavaScript URLs should be blocked."""
        assert is_same_origin("javascript:alert(1)") is False

    def test_data_url_is_blocked(self):
        """Data URLs should be blocked."""
        assert is_same_origin("data:text/html,<script>alert(1)</script>") is False

    def test_none_and_empty_return_true(self):
        """None and empty string should be safe (default fallback)."""
        assert is_same_origin(None) is True
        assert is_same_origin("") is True


class TestSafeRedirect:
    """Test safe_redirect function."""

    def test_valid_relative_url_redirects(self):
        """Valid relative URLs should redirect correctly."""
        result = safe_redirect("/students", "/index")
        assert result == "/students"

    def test_valid_url_with_query_params(self):
        """Relative URLs with query params should work."""
        result = safe_redirect("/students?search=max", "/index")
        assert result == "/students?search=max"

    def test_evil_url_falls_back_to_default(self):
        """Evil URLs should fall back to default_url."""
        result = safe_redirect("http://evil.com", "/index")
        assert "evil.com" not in result
        assert result == "/index"

    def test_javascript_url_falls_back(self):
        """JavaScript URLs should fall back."""
        result = safe_redirect("javascript:alert(1)", "/index")
        assert "javascript" not in result.lower()
        assert result == "/index"

    def test_none_url_falls_back(self):
        """None URL should fall back to default."""
        result = safe_redirect(None, "/index")
        assert result == "/index"

    def test_empty_url_falls_back(self):
        """Empty URL should fall back to default."""
        result = safe_redirect("", "/index")
        assert result == "/index"

    def test_protocol_relative_url_falls_back(self):
        """Protocol-relative URLs should be blocked."""
        result = safe_redirect("//evil.com/phish", "/index")
        assert "evil.com" not in result
        assert result == "/index"

    def test_data_url_falls_back(self):
        """Data URLs should be blocked."""
        result = safe_redirect("data:text/html,<script>", "/index")
        assert "data:" not in result
        assert result == "/index"

    def test_fallback_disabled(self):
        """With fallback_safe=False, empty string returned for unsafe URLs."""
        result = safe_redirect("http://evil.com", "/index", fallback_safe=False)
        assert result == ""
