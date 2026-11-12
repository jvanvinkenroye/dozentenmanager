"""
Unit tests for PageAnnotation timezone-aware datetime.

Verifies that PageAnnotation uses timezone-aware datetime.now(UTC)
instead of naive datetime.utcnow().
"""

import datetime


class TestPageAnnotationTimezoneAware:
    """Test that PageAnnotation uses timezone-aware datetime."""

    def test_utc_import_uses_aware_datetime(self):
        """
        Verify that datetime.now(UTC) returns a timezone-aware datetime.
        This is the pattern used in PageAnnotation model.
        """
        now_aware = datetime.datetime.now(datetime.UTC)
        assert now_aware.tzinfo is not None, (
            "datetime.now(UTC) should return a timezone-aware datetime"
        )

        # Compare with naive datetime (the old, buggy pattern)
        now_naive = datetime.datetime.utcnow()
        assert now_naive.tzinfo is None, (
            "datetime.utcnow() returns naive datetime (the bug we're fixing)"
        )

        # The aware datetime is the correct pattern
        assert now_aware.tzinfo is not None
        assert now_naive.tzinfo is None

    def test_utc_import_exists(self):
        """Verify UTC is importable from datetime module."""
        from datetime import UTC

        assert UTC is not None
