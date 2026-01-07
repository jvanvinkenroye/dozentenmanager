"""
Unit tests for university service and CLI.

This module tests all university management functions.
"""

import pytest

from app.services.university_service import UniversityService


@pytest.fixture
def service():
    """Return a UniversityService instance."""
    return UniversityService()


class TestSlugValidation:
    """Test slug validation function."""

    def test_valid_slug_lowercase(self):
        """Test that lowercase letters are valid."""
        assert UniversityService.validate_slug("technik") is True

    def test_valid_slug_with_numbers(self):
        """Test that numbers are valid."""
        assert UniversityService.validate_slug("th-koeln-2023") is True

    def test_valid_slug_with_hyphens(self):
        """Test that hyphens are valid."""
        assert UniversityService.validate_slug("technische-hochschule") is True

    def test_invalid_slug_uppercase(self):
        """Test that uppercase letters are invalid."""
        assert UniversityService.validate_slug("TH-Koeln") is False

    def test_invalid_slug_spaces(self):
        """Test that spaces are invalid."""
        assert UniversityService.validate_slug("th koeln") is False

    def test_invalid_slug_special_chars(self):
        """Test that special characters are invalid."""
        assert UniversityService.validate_slug("th_koeln") is False
        assert UniversityService.validate_slug("th.koeln") is False
        assert UniversityService.validate_slug("th@koeln") is False

    def test_invalid_slug_leading_hyphen(self):
        """Test that leading hyphens are invalid."""
        assert UniversityService.validate_slug("-th-koeln") is False

    def test_invalid_slug_trailing_hyphen(self):
        """Test that trailing hyphens are invalid."""
        assert UniversityService.validate_slug("th-koeln-") is False

    def test_invalid_slug_double_hyphen(self):
        """Test that double hyphens are invalid."""
        assert UniversityService.validate_slug("th--koeln") is False


class TestSlugGeneration:
    """Test slug generation function."""

    def test_generate_slug_simple(self):
        """Test slug generation from simple name."""
        assert UniversityService.generate_slug("TH Köln") == "th-koeln"

    def test_generate_slug_long_name(self):
        """Test slug generation from long name."""
        assert (
            UniversityService.generate_slug("Technische Hochschule Köln") == "technische-hochschule-koeln"
        )

    def test_generate_slug_with_umlauts(self):
        """Test slug generation with umlauts."""
        assert UniversityService.generate_slug("München") == "muenchen"
        assert UniversityService.generate_slug("Düsseldorf") == "duesseldorf"
        assert UniversityService.generate_slug("Zürich") == "zuerich"

    def test_generate_slug_with_special_chars(self):
        """Test slug generation with special characters."""
        assert UniversityService.generate_slug("TH & FH Köln") == "th-fh-koeln"
        assert UniversityService.generate_slug("Köln (NRW)") == "koeln-nrw"

    def test_generate_slug_removes_multiple_spaces(self):
        """Test that multiple spaces are converted to single hyphen."""
        assert UniversityService.generate_slug("TH  Köln") == "th-koeln"

    def test_generate_slug_removes_leading_trailing_hyphens(self):
        """Test that leading/trailing hyphens are removed."""
        assert UniversityService.generate_slug(" TH Köln ") == "th-koeln"


class TestAddUniversity:
    """Test add_university function."""

    def test_add_university_success(self, app, db, service):
        """Test adding a university successfully."""
        with app.app_context():
            university = service.add_university("TH Köln")

            assert university is not None
            assert university.id is not None
            assert university.name == "TH Köln"
            assert university.slug == "th-koeln"

    def test_add_university_with_custom_slug(self, app, db, service):
        """Test adding a university with custom slug."""
        with app.app_context():
            university = service.add_university("TH Köln", "thk")

            assert university is not None
            assert university.slug == "thk"

    def test_add_university_empty_name(self, app, db, service):
        """Test that empty name raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="cannot be empty"):
                service.add_university("")

            with pytest.raises(ValueError, match="cannot be empty"):
                service.add_university("   ")

    def test_add_university_invalid_slug(self, app, db, service):
        """Test that invalid slug raises ValueError."""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid slug format"):
                service.add_university("TH Köln", "TH Köln")

            with pytest.raises(ValueError, match="Invalid slug format"):
                service.add_university("TH Köln", "th_koeln")

    def test_add_university_duplicate_name(self, app, db, service):
        """Test that duplicate name raises ValueError."""
        with app.app_context():
            service.add_university("TH Köln")

            with pytest.raises(ValueError, match="already exists"):
                service.add_university("TH Köln")

    def test_add_university_duplicate_slug(self, app, db, service):
        """Test that duplicate slug raises ValueError."""
        with app.app_context():
            service.add_university("TH Köln", "th-koeln")

            with pytest.raises(ValueError, match="already exists"):
                service.add_university("Technische Hochschule Köln", "th-koeln")

    def test_add_university_strips_whitespace(self, app, db, service):
        """Test that whitespace is stripped from name and slug."""
        with app.app_context():
            university = service.add_university("  TH Köln  ", "  th-koeln  ")

            assert university.name == "TH Köln"
            assert university.slug == "th-koeln"


class TestListUniversities:
    """Test list_universities function."""

    def test_list_universities_empty(self, app, db, service):
        """Test listing universities when none exist."""
        with app.app_context():
            universities = service.list_universities()
            assert universities == []

    def test_list_universities_multiple(self, app, db, service):
        """Test listing multiple universities."""
        with app.app_context():
            service.add_university("TH Köln")
            service.add_university("RWTH Aachen")
            service.add_university("Uni Bonn")

            universities = service.list_universities()
            assert len(universities) == 3

            # Check alphabetical ordering
            names = [uni.name for uni in universities]
            assert names == sorted(names)

    def test_list_universities_search_by_name(self, app, db, service):
        """Test searching universities by name."""
        with app.app_context():
            service.add_university("TH Köln")
            service.add_university("RWTH Aachen")
            service.add_university("Uni Köln")

            universities = service.list_universities("Köln")
            assert len(universities) == 2

            names = [uni.name for uni in universities]
            assert "TH Köln" in names
            assert "Uni Köln" in names

    def test_list_universities_search_by_slug(self, app, db, service):
        """Test searching universities by slug."""
        with app.app_context():
            service.add_university("TH Köln", "th-koeln")
            service.add_university("RWTH Aachen", "rwth-aachen")

            universities = service.list_universities("rwth")
            assert len(universities) == 1
            assert universities[0].name == "RWTH Aachen"

    def test_list_universities_search_case_insensitive(self, app, db, service):
        """Test that search is case-insensitive."""
        with app.app_context():
            # Note: SQLite has limitations with Unicode case-insensitivity
            # Use ASCII characters for reliable case-insensitive search
            service.add_university("TH Aachen")

            universities = service.list_universities("th aachen")
            assert len(universities) == 1

            universities = service.list_universities("TH AACHEN")
            assert len(universities) == 1


class TestGetUniversity:
    """Test get_university function."""

    def test_get_university_exists(self, app, db, service):
        """Test getting an existing university."""
        with app.app_context():
            created = service.add_university("TH Köln")
            university = service.get_university(created.id)

            assert university is not None
            assert university.id == created.id
            assert university.name == "TH Köln"

    def test_get_university_not_found(self, app, db, service):
        """Test getting a non-existent university."""
        with app.app_context():
            university = service.get_university(999)
            assert university is None


class TestUpdateUniversity:
    """Test update_university function."""

    def test_update_university_name(self, app, db, service):
        """Test updating university name."""
        with app.app_context():
            created = service.add_university("TH Köln")
            updated = service.update_university(created.id, name="Technische Hochschule Köln")

            assert updated is not None
            assert updated.name == "Technische Hochschule Köln"
            assert updated.slug == "th-koeln"  # Slug unchanged

    def test_update_university_slug(self, app, db, service):
        """Test updating university slug."""
        with app.app_context():
            created = service.add_university("TH Köln")
            updated = service.update_university(created.id, slug="thk")

            assert updated is not None
            assert updated.name == "TH Köln"  # Name unchanged
            assert updated.slug == "thk"

    def test_update_university_both(self, app, db, service):
        """Test updating both name and slug."""
        with app.app_context():
            created = service.add_university("TH Köln")
            updated = service.update_university(
                created.id, name="Technische Hochschule Köln", slug="thk"
            )

            assert updated is not None
            assert updated.name == "Technische Hochschule Köln"
            assert updated.slug == "thk"

    def test_update_university_not_found(self, app, db, service):
        """Test updating non-existent university."""
        with app.app_context():
            result = service.update_university(999, name="Test")
            assert result is None

    def test_update_university_no_fields(self, app, db, service):
        """Test that updating without fields raises ValueError."""
        with app.app_context():
            created = service.add_university("TH Köln")

            with pytest.raises(ValueError, match="At least one field"):
                service.update_university(created.id)

    def test_update_university_empty_name(self, app, db, service):
        """Test that empty name raises ValueError."""
        with app.app_context():
            created = service.add_university("TH Köln")

            with pytest.raises(ValueError, match="cannot be empty"):
                service.update_university(created.id, name="")

    def test_update_university_invalid_slug(self, app, db, service):
        """Test that invalid slug raises ValueError."""
        with app.app_context():
            created = service.add_university("TH Köln")

            with pytest.raises(ValueError, match="Invalid slug format"):
                service.update_university(created.id, slug="TH Köln")

    def test_update_university_duplicate_name(self, app, db, service):
        """Test that duplicate name raises ValueError."""
        with app.app_context():
            service.add_university("TH Köln")
            uni2 = service.add_university("RWTH Aachen")

            with pytest.raises(ValueError, match="already exists"):
                service.update_university(uni2.id, name="TH Köln")

    def test_update_university_duplicate_slug(self, app, db, service):
        """Test that duplicate slug raises ValueError."""
        with app.app_context():
            service.add_university("TH Köln", "th-koeln")
            uni2 = service.add_university("RWTH Aachen", "rwth-aachen")

            with pytest.raises(ValueError, match="already exists"):
                service.update_university(uni2.id, slug="th-koeln")


class TestDeleteUniversity:
    """Test delete_university function."""

    def test_delete_university_success(self, app, db, service):
        """Test deleting a university successfully."""
        with app.app_context():
            created = service.add_university("TH Köln")
            result = service.delete_university(created.id)

            assert result is True

            # Verify it's deleted
            university = service.get_university(created.id)
            assert university is None

    def test_delete_university_not_found(self, app, db, service):
        """Test deleting non-existent university."""
        with app.app_context():
            result = service.delete_university(999)
            assert result is False
