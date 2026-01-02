"""
University management CLI tool.

This module provides command-line interface for managing university records,
including adding, updating, listing, and deleting universities.
"""

import argparse
import logging
import re
import sys
from typing import Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db
from app import create_app
from app.models.university import University

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_slug(slug: str) -> bool:
    """
    Validate slug format (lowercase letters, numbers, and hyphens only).

    Args:
        slug: The slug to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    return bool(re.match(pattern, slug))


def generate_slug(name: str) -> str:
    """
    Generate a slug from university name.

    Args:
        name: University name

    Returns:
        Generated slug (lowercase, hyphen-separated)

    Examples:
        >>> generate_slug("Technische Hochschule Köln")
        'technische-hochschule-koeln'
        >>> generate_slug("TH Köln")
        'th-koeln'
    """
    # Convert to lowercase
    slug = name.lower()

    # Replace umlauts and special characters
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
    }
    for char, replacement in replacements.items():
        slug = slug.replace(char, replacement)

    # Remove all non-alphanumeric characters except spaces and hyphens
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)

    # Replace spaces with hyphens
    slug = re.sub(r"\s+", "-", slug)

    # Remove multiple consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    return slug


def add_university(name: str, slug: Optional[str] = None) -> Optional[University]:
    """
    Add a new university to the database.

    Args:
        name: Full name of the university
        slug: URL-friendly identifier (auto-generated if not provided)

    Returns:
        Created University object or None if failed

    Raises:
        ValueError: If name is empty or slug format is invalid
        IntegrityError: If university with same name or slug already exists
    """
    # Validate name
    if not name or not name.strip():
        raise ValueError("University name cannot be empty")

    name = name.strip()

    # Generate or validate slug
    if slug is None:
        slug = generate_slug(name)
        logger.info(f"Auto-generated slug: {slug}")
    else:
        slug = slug.strip().lower()
        if not validate_slug(slug):
            raise ValueError(
                f"Invalid slug format: {slug}. "
                "Slug must contain only lowercase letters, numbers, and hyphens."
            )

    try:
        # Create new university
        university = University(name=name, slug=slug)
        db.session.add(university)
        db.session.commit()

        logger.info(f"Successfully created university: {university}")
        return university

    except IntegrityError as e:
        db.session.rollback()
        if "name" in str(e):
            raise ValueError(f"University with name '{name}' already exists") from e
        elif "slug" in str(e):
            raise ValueError(f"University with slug '{slug}' already exists") from e
        else:
            raise

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while adding university: {e}")
        raise


def list_universities(search: Optional[str] = None) -> list[University]:
    """
    List all universities, optionally filtered by search term.

    Args:
        search: Optional search term to filter by name or slug

    Returns:
        List of University objects
    """
    try:
        query = db.session.query(University)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (University.name.ilike(search_term))
                | (University.slug.ilike(search_term))
            )

        universities = query.order_by(University.name).all()
        logger.info(f"Found {len(universities)} universities")
        return universities

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing universities: {e}")
        raise


def get_university(university_id: int) -> Optional[University]:
    """
    Get a university by ID.

    Args:
        university_id: University ID

    Returns:
        University object or None if not found
    """
    try:
        university = db.session.query(University).filter_by(id=university_id).first()

        if university:
            logger.info(f"Found university: {university}")
        else:
            logger.warning(f"University with ID {university_id} not found")

        return university

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching university: {e}")
        raise


def update_university(
    university_id: int, name: Optional[str] = None, slug: Optional[str] = None
) -> Optional[University]:
    """
    Update a university's information.

    Args:
        university_id: University ID
        name: New name (optional)
        slug: New slug (optional)

    Returns:
        Updated University object or None if not found

    Raises:
        ValueError: If validation fails
        IntegrityError: If updated values conflict with existing records
    """
    if name is None and slug is None:
        raise ValueError(
            "At least one field (name or slug) must be provided for update"
        )

    try:
        university = db.session.query(University).filter_by(id=university_id).first()

        if not university:
            logger.warning(f"University with ID {university_id} not found")
            return None

        # Update fields if provided
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("University name cannot be empty")
            university.name = name

        if slug is not None:
            slug = slug.strip().lower()
            if not validate_slug(slug):
                raise ValueError(
                    f"Invalid slug format: {slug}. "
                    "Slug must contain only lowercase letters, numbers, and hyphens."
                )
            university.slug = slug

        db.session.commit()
        logger.info(f"Successfully updated university: {university}")
        return university

    except IntegrityError as e:
        db.session.rollback()
        if "name" in str(e):
            raise ValueError(f"University with name '{name}' already exists") from e
        elif "slug" in str(e):
            raise ValueError(f"University with slug '{slug}' already exists") from e
        else:
            raise

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while updating university: {e}")
        raise


def delete_university(university_id: int) -> bool:
    """
    Delete a university by ID.

    Args:
        university_id: University ID

    Returns:
        True if deleted, False if not found
    """
    try:
        university = db.session.query(University).filter_by(id=university_id).first()

        if not university:
            logger.warning(f"University with ID {university_id} not found")
            return False

        db.session.delete(university)
        db.session.commit()
        logger.info(f"Successfully deleted university: {university}")
        return True

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while deleting university: {e}")
        raise


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="University management CLI tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new university")
    add_parser.add_argument("--name", required=True, help="University name")
    add_parser.add_argument(
        "--slug", help="URL-friendly slug (auto-generated if omitted)"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List all universities")
    list_parser.add_argument("--search", help="Search by name or slug")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show university details")
    show_parser.add_argument("id", type=int, help="University ID")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update a university")
    update_parser.add_argument("id", type=int, help="University ID")
    update_parser.add_argument("--name", help="New university name")
    update_parser.add_argument("--slug", help="New slug")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a university")
    delete_parser.add_argument("id", type=int, help="University ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create Flask app context for database access
    app = create_app()

    with app.app_context():
        try:
            if args.command == "add":
                university = add_university(args.name, args.slug)
                if university:  # Should always be true, but satisfies type checker
                    print(
                        f"Created university: ID={university.id}, Name={university.name}, Slug={university.slug}"
                    )
                return 0

            elif args.command == "list":
                universities = list_universities(args.search)
                if universities:
                    print(f"\nFound {len(universities)} universities:\n")
                    print(f"{'ID':<5} {'Name':<40} {'Slug':<30}")
                    print("-" * 75)
                    for uni in universities:
                        print(f"{uni.id:<5} {uni.name:<40} {uni.slug:<30}")
                else:
                    print("No universities found")
                return 0

            elif args.command == "show":
                university = get_university(args.id)
                if university:
                    print("\nUniversity Details:")
                    print(f"  ID: {university.id}")
                    print(f"  Name: {university.name}")
                    print(f"  Slug: {university.slug}")
                    print(f"  Created: {university.created_at}")
                    print(f"  Updated: {university.updated_at}")
                else:
                    print(f"University with ID {args.id} not found")
                    return 1
                return 0

            elif args.command == "update":
                university = update_university(args.id, args.name, args.slug)
                if university:
                    print(
                        f"Updated university: ID={university.id}, Name={university.name}, Slug={university.slug}"
                    )
                    return 0
                else:
                    print(f"University with ID {args.id} not found")
                    return 1

            elif args.command == "delete":
                if delete_university(args.id):
                    print(f"University with ID {args.id} deleted successfully")
                    return 0
                else:
                    print(f"University with ID {args.id} not found")
                    return 1

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
