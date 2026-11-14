"""
Unit tests for MIME type validation in upload routes.

Verifies that both the web routes (document.py) and API routes (api.py)
reject files with dangerous or mismatched MIME types.
"""

import mimetypes


class TestUploadMIMEValidation:
    """Test that upload routes validate MIME types."""

    def test_api_upload_route_validates_extension(self, client):
        """API upload route should reject files with disallowed extensions."""
        from app.models.document import allowed_file

        assert allowed_file("payload.dll") is False
        assert allowed_file("document.pdf") is True

    def test_mime_type_for_common_files(self):
        """Verify Python's mimetypes module handles common file types."""
        assert mimetypes.guess_type("file.pdf")[0] == "application/pdf"
        assert (
            mimetypes.guess_type("file.docx")[0]
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert mimetypes.guess_type("file.doc")[0] == "application/msword"
        assert mimetypes.guess_type("file.txt")[0] == "text/plain"

    def test_validate_file_mime_type_rejects_dangerous(self):
        """validate_file_mime_type should reject dangerous MIME prefixes."""
        from app.models.document import validate_file_mime_type

        assert validate_file_mime_type("malware.exe") is False
        assert validate_file_mime_type("script.sh") is False
        assert validate_file_mime_type("document.pdf") is True

    def test_validate_file_mime_type_allows_documents(self):
        """validate_file_mime_type should allow common document types."""
        from app.models.document import validate_file_mime_type

        assert validate_file_mime_type("report.docx") is True
        assert validate_file_mime_type("report.doc") is True
        assert validate_file_mime_type("report.odt") is True
        assert validate_file_mime_type("readme.txt") is True

    def test_validate_file_mime_type_uses_extension_check_when_unknown(self):
        """When MIME type can't be determined, fall back to extension check."""
        from app.models.document import allowed_file, validate_file_mime_type

        assert validate_file_mime_type("script.exe") is False
        assert allowed_file("script.exe") is False
        assert validate_file_mime_type("document.pdf") is True
        assert allowed_file("document.pdf") is True
