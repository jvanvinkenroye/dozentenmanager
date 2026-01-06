"""
Document model for Dozentenmanager.

This module defines the Document model representing uploaded files
associated with submissions.
"""

import os
import re
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Index
from app import db
from app.models.base import TimestampMixin


# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "odt", "rtf"}

# Maximum filename length
MAX_FILENAME_LENGTH = 255

# Maximum file path length
MAX_FILEPATH_LENGTH = 500


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other security issues.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem use

    Examples:
        >>> sanitize_filename("../../../etc/passwd")
        'etc_passwd'
        >>> sanitize_filename("my file (1).pdf")
        'my_file_1.pdf'
        >>> sanitize_filename("<script>alert('xss')</script>.pdf")
        'scriptalertxssscript.pdf'
    """
    if not filename:
        return "unnamed_file"

    # Get basename to remove any path components
    filename = os.path.basename(filename)

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Split into name and extension
    name, ext = os.path.splitext(filename)

    # Remove dangerous characters (keep only alphanumeric, underscore, hyphen, dot)
    name = re.sub(r"[^\w\s\-]", "", name)

    # Replace spaces and multiple underscores with single underscore
    name = re.sub(r"[\s_]+", "_", name)

    # Remove leading/trailing underscores and hyphens
    name = name.strip("_-")

    # Ensure name is not empty
    if not name:
        name = "unnamed"

    # Sanitize extension
    ext = ext.lower()
    ext = re.sub(r"[^\w.]", "", ext)

    # Combine and truncate if necessary
    result = f"{name}{ext}"
    if len(result) > MAX_FILENAME_LENGTH:
        # Truncate name, keep extension
        max_name_len = MAX_FILENAME_LENGTH - len(ext)
        name = name[:max_name_len]
        result = f"{name}{ext}"

    return result


def allowed_file(filename: str) -> bool:
    """
    Check if file extension is allowed.

    Args:
        filename: Filename to check

    Returns:
        True if extension is allowed, False otherwise

    Examples:
        >>> allowed_file("document.pdf")
        True
        >>> allowed_file("script.exe")
        False
        >>> allowed_file("no_extension")
        False
    """
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename.

    Args:
        filename: Filename to get extension from

    Returns:
        Lowercase file extension without dot, or empty string

    Examples:
        >>> get_file_extension("document.PDF")
        'pdf'
        >>> get_file_extension("file.tar.gz")
        'gz'
        >>> get_file_extension("no_extension")
        ''
    """
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


class Document(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """
    Document model representing an uploaded file.

    Attributes:
        id: Unique document identifier
        submission_id: Foreign key to Submission
        filename: Sanitized filename for storage
        original_filename: Original filename as uploaded
        file_path: Full path to the file on disk
        file_type: File extension (e.g., 'pdf', 'docx')
        file_size: File size in bytes
        mime_type: MIME type of the file
        upload_date: Date and time when file was uploaded
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "document"

    id = Column(Integer, primary_key=True)
    submission_id = Column(
        Integer, ForeignKey("submission.id"), nullable=False, index=True
    )
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    file_type = Column(String(10), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=True)
    upload_date = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_document_submission", "submission_id"),
        Index("idx_document_file_type", "file_type"),
    )

    def __repr__(self) -> str:
        """String representation of Document."""
        return (
            f"<Document(id={self.id}, filename='{self.filename}', "
            f"type='{self.file_type}', size={self.file_size})>"
        )

    def to_dict(self) -> dict:
        """
        Convert Document instance to dictionary.

        Returns:
            Dictionary representation of the document
        """
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "upload_date": (
                self.upload_date.isoformat() if self.upload_date else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def file_size_human(self) -> str:
        """
        Get human-readable file size.

        Returns:
            File size in human-readable format (e.g., '1.5 MB')
        """
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
