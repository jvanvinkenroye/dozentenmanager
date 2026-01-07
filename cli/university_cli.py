"""
University management CLI tool.

This module provides command-line interface for managing university records,
including adding, updating, listing, and deleting universities.
"""

import argparse
import logging
import sys

from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.services.university_service import UniversityService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
        # Initialize service
        service = UniversityService()

        try:
            if args.command == "add":
                university = service.add_university(args.name, args.slug)
                print(
                    f"Created university: ID={university.id}, Name={university.name}, Slug={university.slug}"
                )
                return 0

            if args.command == "list":
                universities = service.list_universities(args.search)
                if universities:
                    print(f"\nFound {len(universities)} universities:\n")
                    print(f"{'ID':<5} {'Name':<40} {'Slug':<30}")
                    print("-" * 75)
                    for uni in universities:
                        print(f"{uni.id:<5} {uni.name:<40} {uni.slug:<30}")
                else:
                    print("No universities found")
                return 0

            if args.command == "show":
                university = service.get_university(args.id)
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

            if args.command == "update":
                university = service.update_university(args.id, args.name, args.slug)
                if university:
                    print(
                        f"Updated university: ID={university.id}, Name={university.name}, Slug={university.slug}"
                    )
                    return 0
                print(f"University with ID {args.id} not found")
                return 1

            if args.command == "delete":
                if service.delete_university(args.id):
                    print(f"University with ID {args.id} deleted successfully")
                    return 0
                print(f"University with ID {args.id} not found")
                return 1

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}", exc_info=True)
            print("Database error. Please try again.", file=sys.stderr)
            return 1

        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            print("\nOperation cancelled.", file=sys.stderr)
            return 130

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
