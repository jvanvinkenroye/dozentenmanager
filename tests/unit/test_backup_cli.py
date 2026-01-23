"""
Unit tests for backup CLI tool.

This module contains tests for backup creation and restoration functionality.
"""

import json
import tempfile
from pathlib import Path
from zipfile import ZipFile

import pytest

from app.models import Course, Student, University
from cli.backup_cli import (
    BACKUP_VERSION,
    create_backup,
    export_database_to_json,
    restore_backup,
    serialize_model,
)


class TestSerializeModel:
    """Tests for model serialization."""

    def test_serialize_student(self, app, db):
        """Test serializing a student model."""
        student = Student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Computer Science",
        )
        db.session.add(student)
        db.session.commit()

        result = serialize_model(student)

        assert result["first_name"] == "Max"
        assert result["last_name"] == "Mustermann"
        assert result["student_id"] == "12345678"
        assert result["email"] == "max@example.com"
        assert result["program"] == "Computer Science"
        assert "id" in result
        assert "created_at" in result

    def test_serialize_with_datetime(self, app, db):
        """Test that datetime fields are properly serialized."""
        university = University(name="Test University", slug="test-university")
        db.session.add(university)
        db.session.commit()

        result = serialize_model(university)

        # Should have ISO format datetime strings
        assert isinstance(result["created_at"], str)
        assert "T" in result["created_at"]


class TestExportDatabase:
    """Tests for database export functionality."""

    def test_export_empty_database(self, app, db):
        """Test exporting an empty database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.json"

            export_database_to_json(output_path)

            assert output_path.exists()

            with output_path.open("r") as f:
                data = json.load(f)

            assert data["version"] == BACKUP_VERSION
            assert "timestamp" in data
            assert "tables" in data
            assert len(data["tables"]["students"]) == 0
            assert len(data["tables"]["universities"]) == 0

    def test_export_with_data(self, app, db):
        """Test exporting database with sample data."""
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

        course = Course(
            name="Introduction to Programming",
            slug="intro-programming",
            semester="2024_WiSe",
            university_id=1,
        )
        db.session.add(course)

        db.session.commit()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_export.json"

            export_database_to_json(output_path)

            with output_path.open("r") as f:
                data = json.load(f)

            assert len(data["tables"]["universities"]) == 1
            assert len(data["tables"]["students"]) == 1
            assert len(data["tables"]["courses"]) == 1

            # Verify student data
            student_data = data["tables"]["students"][0]
            assert student_data["first_name"] == "Max"
            assert student_data["student_id"] == "12345678"


class TestCreateBackup:
    """Tests for backup creation functionality."""

    def test_create_backup_no_uploads(self, app, db):
        """Test creating a backup without uploaded files."""
        # Create test data
        student = Student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Computer Science",
        )
        db.session.add(student)
        db.session.commit()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = str(Path(temp_dir) / "test_backup.zip")

            backup_path = create_backup(output_file, include_uploads=False)

            assert backup_path.exists()
            assert backup_path.suffix == ".zip"

            # Verify archive contents
            with ZipFile(backup_path, "r") as zipf:
                files = zipf.namelist()
                assert "database.json" in files

                # Extract and verify database.json
                with zipf.open("database.json") as f:
                    data = json.load(f)
                    assert data["version"] == BACKUP_VERSION
                    assert len(data["tables"]["students"]) == 1

    def test_create_backup_with_uploads(self, app, db):
        """Test creating a backup including uploaded files."""
        # Create uploads directory with test file
        upload_folder = Path("uploads")
        upload_folder.mkdir(parents=True, exist_ok=True)

        test_file = upload_folder / "test_document.txt"
        test_file.write_text("Test document content")

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = str(Path(temp_dir) / "test_backup.zip")

                backup_path = create_backup(output_file, include_uploads=True)

                assert backup_path.exists()

                # Verify archive includes uploads
                with ZipFile(backup_path, "r") as zipf:
                    files = zipf.namelist()
                    assert "database.json" in files
                    assert "uploads/test_document.txt" in files

        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()

    def test_backup_filename_generation(self, app, db):
        """Test that backup filename includes timestamp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = str(Path(temp_dir) / "mybackup")

            backup_path = create_backup(output_file, include_uploads=False)

            # Should have added timestamp and .zip extension
            assert backup_path.name.startswith("mybackup_")
            assert backup_path.suffix == ".zip"


class TestRestoreBackup:
    """Tests for backup restoration functionality."""

    def test_restore_backup_basic(self, app, db):
        """Test restoring a basic backup."""
        # Create original data
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
            create_backup(backup_file, include_uploads=False)

            # Clear database
            db.session.query(Student).delete()
            db.session.commit()

            assert Student.query.count() == 0

            # Restore backup
            restore_backup(backup_file, clear_existing=False)

            # Verify data restored
            students = Student.query.all()
            assert len(students) == 1
            assert students[0].first_name == "Max"
            assert students[0].student_id == "12345678"

    def test_restore_with_clear_existing(self, app, db):
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
            create_backup(backup_file, include_uploads=False)

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
            restore_backup(backup_file, clear_existing=True)

            # Should only have original student
            students = Student.query.all()
            assert len(students) == 1
            assert students[0].first_name == "Max"

    def test_restore_invalid_file(self, app, db):
        """Test error handling for invalid backup file."""
        with pytest.raises(ValueError, match="Backup file not found"):
            restore_backup("nonexistent.zip", clear_existing=False)

    def test_restore_invalid_format(self, app, db):
        """Test error handling for non-ZIP file."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as temp_file:
            with pytest.raises(ValueError, match="Invalid backup file format"):
                restore_backup(temp_file.name, clear_existing=False)

    def test_restore_missing_database_json(self, app, db):
        """Test error handling for backup without database.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_file = Path(temp_dir) / "invalid_backup.zip"

            # Create ZIP without database.json
            with ZipFile(backup_file, "w") as zipf:
                zipf.writestr("some_file.txt", "test content")

            with pytest.raises(ValueError, match="database.json not found"):
                restore_backup(str(backup_file), clear_existing=False)

    def test_restore_with_files(self, app, db):
        """Test restoring backup with uploaded files."""
        # Create uploads directory with test file
        upload_folder = Path("uploads")
        upload_folder.mkdir(parents=True, exist_ok=True)

        test_subfolder = upload_folder / "test_course"
        test_subfolder.mkdir(parents=True, exist_ok=True)

        test_file = test_subfolder / "document.txt"
        test_file.write_text("Original content")

        try:
            # Create backup
            with tempfile.TemporaryDirectory() as temp_dir:
                backup_file = str(Path(temp_dir) / "test_backup.zip")
                create_backup(backup_file, include_uploads=True)

                # Remove the file
                test_file.unlink()
                assert not test_file.exists()

                # Restore backup
                restore_backup(backup_file, clear_existing=False)

                # Verify file restored
                assert test_file.exists()
                assert test_file.read_text() == "Original content"

        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
            if test_subfolder.exists():
                test_subfolder.rmdir()


class TestBackupRestore:
    """Integration tests for complete backup and restore workflow."""

    def test_full_backup_restore_cycle(self, app, db):
        """Test complete backup and restore cycle with multiple models."""
        # Create comprehensive test data
        university = University(
            name="Test University", slug="test-university"
        )
        db.session.add(university)
        db.session.flush()

        student = Student(
            first_name="Max",
            last_name="Mustermann",
            student_id="12345678",
            email="max@example.com",
            program="Computer Science",
        )
        db.session.add(student)

        course = Course(
            name="Introduction to Programming",
            slug="intro-programming",
            semester="2024_WiSe",
            university_id=university.id,
        )
        db.session.add(course)

        db.session.commit()

        # Record counts before backup
        uni_count = University.query.count()
        student_count = Student.query.count()
        course_count = Course.query.count()

        # Create backup
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_file = str(Path(temp_dir) / "full_backup.zip")
            create_backup(backup_file, include_uploads=False)

            # Clear all data
            db.session.query(Course).delete()
            db.session.query(Student).delete()
            db.session.query(University).delete()
            db.session.commit()

            assert University.query.count() == 0
            assert Student.query.count() == 0
            assert Course.query.count() == 0

            # Restore backup
            restore_backup(backup_file, clear_existing=False)

            # Verify all data restored
            assert University.query.count() == uni_count
            assert Student.query.count() == student_count
            assert Course.query.count() == course_count

            # Verify data integrity
            restored_uni = University.query.first()
            assert restored_uni.name == "Test University"
            assert restored_uni.slug == "test-university"

            restored_student = Student.query.first()
            assert restored_student.first_name == "Max"
            assert restored_student.student_id == "12345678"

            restored_course = Course.query.first()
            assert restored_course.name == "Introduction to Programming"
            assert restored_course.slug == "intro-programming"
