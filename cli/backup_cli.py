"""
Backup and restore CLI tool.

This module provides command-line interface for backing up and restoring
all data including database records and uploaded files.
"""

import argparse
import contextlib
import json
import logging
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from sqlalchemy.exc import SQLAlchemyError

from app import create_app, db
from app.models import (
    Course,
    Document,
    Enrollment,
    Exam,
    ExamComponent,
    Grade,
    GradeThreshold,
    GradingScale,
    Student,
    Submission,
    University,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Backup format version for compatibility checking
BACKUP_VERSION = "1.0"


def serialize_model(obj: Any) -> dict[str, Any]:
    """
    Serialize a SQLAlchemy model instance to a dictionary.

    Args:
        obj: SQLAlchemy model instance

    Returns:
        Dictionary representation of the model
    """
    data = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        # Convert datetime objects to ISO format strings
        if isinstance(value, datetime):
            value = value.isoformat()
        data[column.name] = value
    return data


def export_database_to_json(output_path: Path) -> None:
    """
    Export all database tables to a JSON file.

    Args:
        output_path: Path where JSON file should be saved

    Raises:
        SQLAlchemyError: If database query fails
        IOError: If file cannot be written
    """
    logger.info("Exporting database to JSON...")

    # Define the order of tables to ensure proper foreign key handling during restore
    tables = [
        ("universities", University),
        ("students", Student),
        ("courses", Course),
        ("enrollments", Enrollment),
        ("exams", Exam),
        ("exam_components", ExamComponent),
        ("grading_scales", GradingScale),
        ("grade_thresholds", GradeThreshold),
        ("grades", Grade),
        ("submissions", Submission),
        ("documents", Document),
    ]

    backup_data = {
        "version": BACKUP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "tables": {},
    }

    for table_name, model in tables:
        try:
            records = model.query.all()
            backup_data["tables"][table_name] = [
                serialize_model(record) for record in records
            ]
            logger.info(f"Exported {len(records)} records from {table_name}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to export {table_name}: {e}")
            raise

    # Write JSON file
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Database exported to {output_path}")


def create_backup(output_file: str, include_uploads: bool = True) -> Path:
    """
    Create a backup archive containing database and uploaded files.

    Args:
        output_file: Name of the backup file (without extension)
        include_uploads: Whether to include uploaded files

    Returns:
        Path to the created backup archive

    Raises:
        SQLAlchemyError: If database export fails
        IOError: If file operations fail
    """
    logger.info("Starting backup process...")

    # Create temporary directory for backup preparation
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Export database to JSON
        db_json_path = temp_path / "database.json"
        export_database_to_json(db_json_path)

        # Create backup archive
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        if not output_file.endswith(".zip"):
            output_file = f"{output_file}_{timestamp}.zip"

        backup_path = Path(output_file)

        with ZipFile(backup_path, "w") as zipf:
            # Add database JSON
            zipf.write(db_json_path, "database.json")

            # Add uploaded files if requested
            if include_uploads:
                upload_folder = Path("uploads")
                if upload_folder.exists():
                    logger.info("Including uploaded files in backup...")
                    for file_path in upload_folder.rglob("*"):
                        if file_path.is_file() and file_path.name != ".gitkeep":
                            # Store with relative path from uploads folder
                            arcname = str(file_path.relative_to(upload_folder.parent))
                            zipf.write(file_path, arcname)
                            logger.debug(f"Added {arcname} to backup")
                    logger.info("Uploaded files added to backup")
                else:
                    logger.warning("Uploads folder not found, skipping files")

    logger.info(f"Backup created successfully: {backup_path}")
    return backup_path


def restore_backup(backup_file: str, clear_existing: bool = False) -> None:
    """
    Restore database and files from a backup archive.

    Args:
        backup_file: Path to the backup ZIP file
        clear_existing: Whether to clear existing data before restore

    Raises:
        ValueError: If backup file is invalid or version incompatible
        SQLAlchemyError: If database operations fail
        IOError: If file operations fail
    """
    logger.info(f"Starting restore from {backup_file}...")

    backup_path = Path(backup_file)
    if not backup_path.exists():
        raise ValueError(f"Backup file not found: {backup_file}")

    if not backup_path.suffix == ".zip":
        raise ValueError(f"Invalid backup file format: {backup_file}")

    # Extract backup to temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        with ZipFile(backup_path, "r") as zipf:
            zipf.extractall(temp_path)

        # Check for database.json
        db_json_path = temp_path / "database.json"
        if not db_json_path.exists():
            raise ValueError("Invalid backup: database.json not found")

        # Load backup data
        with db_json_path.open("r", encoding="utf-8") as f:
            backup_data = json.load(f)

        # Check version compatibility
        if backup_data.get("version") != BACKUP_VERSION:
            logger.warning(
                f"Backup version {backup_data.get('version')} "
                f"may not be compatible with current version {BACKUP_VERSION}"
            )

        # Clear existing data if requested
        if clear_existing:
            logger.info("Clearing existing data...")
            _clear_database()

        # Restore database tables
        _restore_database_tables(backup_data["tables"])

        # Restore uploaded files
        uploads_path = temp_path / "uploads"
        if uploads_path.exists():
            logger.info("Restoring uploaded files...")
            upload_folder = Path("uploads")
            upload_folder.mkdir(parents=True, exist_ok=True)

            for file_path in uploads_path.rglob("*"):
                if file_path.is_file():
                    # Recreate directory structure
                    relative_path = file_path.relative_to(uploads_path)
                    target_path = upload_folder / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(file_path, target_path)
                    logger.debug(f"Restored file: {relative_path}")

            logger.info("Uploaded files restored")

    logger.info("Restore completed successfully")


def _clear_database() -> None:
    """
    Clear all data from database tables.

    Raises:
        SQLAlchemyError: If database operations fail
    """
    # Delete in reverse order to handle foreign keys
    models = [
        Document,
        Submission,
        Grade,
        GradeThreshold,
        GradingScale,
        ExamComponent,
        Exam,
        Enrollment,
        Course,
        Student,
        University,
    ]

    for model in models:
        try:
            db.session.query(model).delete()
            logger.info(f"Cleared {model.__tablename__}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to clear {model.__tablename__}: {e}")
            db.session.rollback()
            raise

    db.session.commit()


def _restore_database_tables(tables_data: dict[str, list[dict[str, Any]]]) -> None:
    """
    Restore database tables from backup data.

    Args:
        tables_data: Dictionary mapping table names to lists of records

    Raises:
        SQLAlchemyError: If database operations fail
    """
    # Map table names to models
    table_models = {
        "universities": University,
        "students": Student,
        "courses": Course,
        "enrollments": Enrollment,
        "exams": Exam,
        "exam_components": ExamComponent,
        "grading_scales": GradingScale,
        "grade_thresholds": GradeThreshold,
        "grades": Grade,
        "submissions": Submission,
        "documents": Document,
    }

    for table_name, records in tables_data.items():
        if table_name not in table_models:
            logger.warning(f"Unknown table in backup: {table_name}, skipping")
            continue

        model = table_models[table_name]
        logger.info(f"Restoring {len(records)} records to {table_name}...")

        for record_data in records:
            try:
                # Convert datetime strings back to datetime objects
                for key, value in record_data.items():
                    if isinstance(value, str) and "T" in value:
                        # Try to parse as datetime
                        with contextlib.suppress(ValueError):
                            record_data[key] = datetime.fromisoformat(value)

                # Create model instance
                instance = model(**record_data)
                db.session.add(instance)
            except Exception as e:
                logger.error(f"Failed to restore record in {table_name}: {e}")
                logger.debug(f"Record data: {record_data}")
                db.session.rollback()
                raise

        try:
            db.session.commit()
            logger.info(f"Restored {len(records)} records to {table_name}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to commit {table_name}: {e}")
            db.session.rollback()
            raise


def main() -> None:
    """Main entry point for the backup CLI tool."""
    parser = argparse.ArgumentParser(
        description="Backup and restore Dozentenmanager data"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a backup")
    backup_parser.add_argument(
        "-o",
        "--output",
        default="backup",
        help="Output file name (default: backup_TIMESTAMP.zip)",
    )
    backup_parser.add_argument(
        "--no-uploads",
        action="store_true",
        help="Exclude uploaded files from backup",
    )

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from a backup")
    restore_parser.add_argument("backup_file", help="Path to backup ZIP file")
    restore_parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before restoring",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create Flask app context
    app = create_app()

    with app.app_context():
        try:
            if args.command == "backup":
                backup_path = create_backup(
                    args.output, include_uploads=not args.no_uploads
                )
                print(f"✓ Backup created: {backup_path}")
                sys.exit(0)

            elif args.command == "restore":
                restore_backup(args.backup_file, clear_existing=args.clear)
                print("✓ Restore completed successfully")
                sys.exit(0)

        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
