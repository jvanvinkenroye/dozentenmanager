"""Tests for file-size limit and 413 error handler."""

from config import Config


class TestConfigFileSizeLimit:
    """Test that MAX_CONTENT_LENGTH is configured."""

    def test_max_content_length_configured(self):
        """Test that MAX_CONTENT_LENGTH is set (not None, not unlimited)."""
        cfg = Config()
        assert cfg.MAX_CONTENT_LENGTH is not None
        assert cfg.MAX_CONTENT_LENGTH > 0

    def test_max_content_length_default_is_50_mb(self):
        """Verify the code defaults to 50 MB by checking the source."""
        import inspect

        source = inspect.getsource(Config)
        # The default in the code should be 50 MB
        assert "50 * 1024 * 1024" in source or "52428800" in source

    def test_max_content_length_via_flask_app(self, client):
        """Test that MAX_CONTENT_LENGTH is applied to the Flask app config."""
        from app import create_app

        app = create_app("testing")
        assert app.config.get("MAX_CONTENT_LENGTH") is not None
        assert app.config["MAX_CONTENT_LENGTH"] > 0


class TestErrorhandler413:
    """Test that 413 error handler is registered."""

    def test_errorhandler_413_registered(self):
        """Test that the 413 error handler exists and is registered."""
        from app import create_app

        app = create_app("testing")
        assert 413 in app.error_handler_spec[None]

    def test_errorhandler_413_handler_function(self):
        """Test that the 413 handler is a valid callable."""
        from app import create_app

        app = create_app("testing")
        handler = app.error_handler_spec[None][413]
        assert len(handler) == 1  # One exception class mapped
        exc_class = next(iter(handler))
        assert handler[exc_class] is not None
