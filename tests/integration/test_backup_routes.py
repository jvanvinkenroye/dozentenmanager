"""
Integration tests for backup routes.

This module tests the Flask web interface for backup management.
"""

import io
import tempfile
from pathlib import Path
from zipfile import ZipFile

from app.models import Student, University
from cli.backup_cli import create_backup


class TestBackupIndexRoute:
    """Test backup management page route."""

    def test_index_loads(self, app, auth_client):
        """Test that backup page loads successfully."""
        response = auth_client.get("/backup/")
        assert response.status_code == 200
        assert b"Backup Management" in response.data
        assert b"Create Backup" in response.data
        assert b"Restore Backup" in response.data


class TestBackupCreateRoute:
    """Test backup creation route."""

    def test_create_backup_no_data(self, app, auth_client):
        """Test creating backup with no data."""
        response = auth_client.post(
            "/backup/create",
            data={"include_uploads": "on"},
            follow_redirects=False,
        )

        # Should return a file
        assert response.status_code == 200
        assert response.mimetype == "application/zip"
        assert "dozentenmanager_backup_" in response.headers.get(
            "Content-Disposition", ""
        )

    def test_create_backup_with_data(self, app, auth_client, db):
        """Test creating backup with sample data."""
        # Create test data
        university = University(name="Test University", slug="test-university")
        db.session.add(university)

        student = Student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Computer Science",
        )
        db.session.add(student)
        db.session.commit()

        response = auth_client.post(
            "/backup/create",
            data={"include_uploads": "on"},
            follow_redirects=False,
        )

        # Should return a file
        assert response.status_code == 200
        assert response.mimetype == "application/zip"

        # Verify ZIP contents
        zip_data = io.BytesIO(response.data)
        with ZipFile(zip_data, "r") as zipf:
            files = zipf.namelist()
            assert "database.json" in files

    def test_create_backup_without_uploads(self, app, auth_client):
        """Test creating backup without uploaded files."""
        response = auth_client.post(
            "/backup/create",
            data={},  # Don't include include_uploads checkbox
            follow_redirects=False,
        )

        # Should still return a file
        assert response.status_code == 200
        assert response.mimetype == "application/zip"


class TestBackupRestoreRoute:
    """Test backup restoration route."""

    def test_restore_no_file(self, app, auth_client):
        """Test restore without providing a file."""
        response = auth_client.post("/backup/restore", data={}, follow_redirects=True)

        assert response.status_code == 200
        assert b"No backup file provided" in response.data

    def test_restore_empty_filename(self, app, auth_client):
        """Test restore with empty filename."""
        response = auth_client.post(
            "/backup/restore",
            data={"backup_file": (io.BytesIO(b""), "")},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"No backup file selected" in response.data

    def test_restore_invalid_format(self, app, auth_client):
        """Test restore with non-ZIP file."""
        response = auth_client.post(
            "/backup/restore",
            data={
                "backup_file": (io.BytesIO(b"not a zip"), "test.txt"),
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Invalid file format" in response.data

    def test_restore_valid_backup(self, app, auth_client, db):
        """Test restoring a valid backup file."""
        # Create original data
        university = University(name="Test University", slug="test-university")
        db.session.add(university)

        student = Student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Computer Science",
        )
        db.session.add(student)
        db.session.commit()

        # Create backup
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_file = str(Path(temp_dir) / "test_backup.zip")
            backup_path = create_backup(backup_file, include_uploads=False)

            # Clear data
            db.session.query(Student).delete()
            db.session.query(University).delete()
            db.session.commit()

            assert Student.query.count() == 0
            assert University.query.count() == 0

            # Restore via web interface
            with open(backup_path, "rb") as f:
                response = auth_client.post(
                    "/backup/restore",
                    data={
                        "backup_file": (f, "test_backup.zip"),
                        "clear_existing": "",  # Don't clear
                    },
                    follow_redirects=True,
                )

            assert response.status_code == 200
            assert b"Backup restored successfully" in response.data

            # Verify data restored
            assert Student.query.count() == 1
            assert University.query.count() == 1

    def test_restore_with_clear_existing(self, app, auth_client, db):
        """Test restoring backup with clear_existing flag."""
        # Create original data
        student1 = Student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Computer Science",
        )
        db.session.add(student1)
        db.session.commit()

        # Create backup
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_file = str(Path(temp_dir) / "test_backup.zip")
            backup_path = create_backup(backup_file, include_uploads=False)

            # Add new student after backup
            student2 = Student(
                first_name="Jane",
                last_name="Doe",
                student_id="87654321",
                email="jane@example.com",
                program="Mathematics",
            )
            db.session.add(student2)
            db.session.commit()

            assert Student.query.count() == 2

            # Restore with clear
            with open(backup_path, "rb") as f:
                response = auth_client.post(
                    "/backup/restore",
                    data={
                        "backup_file": (f, "test_backup.zip"),
                        "clear_existing": "on",  # Clear existing
                    },
                    follow_redirects=True,
                )

            assert response.status_code == 200
            assert b"Backup restored successfully" in response.data

            # Should only have original student
            students = Student.query.all()
            assert len(students) == 1
            assert students[0].first_name == "Max"

    def test_restore_invalid_backup_file(self, app, auth_client):
        """Test restore with invalid backup ZIP."""
        # Create a ZIP without database.json
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_zip = Path(temp_dir) / "invalid.zip"
            with ZipFile(invalid_zip, "w") as zipf:
                zipf.writestr("some_file.txt", "test content")

            with open(invalid_zip, "rb") as f:
                response = auth_client.post(
                    "/backup/restore",
                    data={
                        "backup_file": (f, "invalid.zip"),
                    },
                    follow_redirects=True,
                )

            assert response.status_code == 200
            assert b"Invalid backup file" in response.data or b"Error" in response.data
