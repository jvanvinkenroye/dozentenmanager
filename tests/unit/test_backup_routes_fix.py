"""
Unit tests for backup routes fix.

This module verifies that the backup index route loads correctly,
and that the conftest.py fixtures are properly configured for backup tests.
"""

import io
import tempfile
from pathlib import Path
from zipfile import ZipFile

import pytest

from app.models import Student, University
from cli.backup_cli import create_backup


class TestBackupIndexUnit:
    """Unit tests for backup index route."""

    def test_index_route_accessible(self, auth_client):
        """Test that backup index route returns 200."""
        response = auth_client.get("/backup/")
        assert response.status_code == 200

    def test_index_contains_expected_content(self, auth_client):
        """Test that backup index page contains expected text."""
        response = auth_client.get("/backup/")
        assert b"Backup Management" in response.data
        assert b"Create Backup" in response.data
        assert b"Restore Backup" in response.data


class TestBackupCliUnit:
    """Unit tests for backup CLI functionality."""

    def test_create_backup_empty_db(self, app, db):
        """Test creating a backup with an empty database."""
        with app.app_context():
            with db.session.begin():
                db.create_all()

        with app.app_context():
            with tempfile.TemporaryDirectory() as temp_dir:
                backup_path = str(Path(temp_dir) / "empty_backup.zip")
                result_path = create_backup(backup_path, include_uploads=False)

                assert Path(result_path).exists()

                with ZipFile(result_path, "r") as zipf:
                    assert "database.json" in zipf.namelist()

    def test_create_backup_with_data(self, app, db):
        """Test creating a backup with sample data."""
        university = University(name="Unit Test Uni", slug="unit-test")
        db.session.add(university)

        student = Student(
            first_name="Unit",
            last_name="Tester",
            student_id="99999999",
            email="unit@test.com",
            program="Testing",
        )
        db.session.add(student)
        db.session.commit()

        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = str(Path(temp_dir) / "data_backup.zip")
            result_path = create_backup(backup_path, include_uploads=False)

            zip_data = io.BytesIO(Path(result_path).read_bytes())
            with ZipFile(zip_data, "r") as zipf:
                files = zipf.namelist()
                assert "database.json" in files
