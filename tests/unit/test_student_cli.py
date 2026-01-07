"""
Unit tests for student service and CLI.

This module tests all student management functions.
"""

import pytest

from app.models.student import validate_email, validate_student_id
from app.services.student_service import StudentService


@pytest.fixture
def service():
    """Return a StudentService instance."""
    return StudentService()


class TestValidationFunctions:
    """Test validation helper functions."""

    def test_validate_email_valid(self):
        """Test that valid email addresses pass validation."""
        assert validate_email("student@example.com") is True
        assert validate_email("test.user@university.edu") is True
        assert validate_email("first.last+tag@domain.co.uk") is True

    def test_validate_email_invalid(self):
        """Test that invalid email addresses fail validation."""
        assert validate_email("invalid-email") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("user domain.com") is False

    def test_validate_student_id_valid(self):
        """Test that valid student IDs pass validation."""
        assert validate_student_id("12345678") is True
        assert validate_student_id("00000000") is True
        assert validate_student_id("99999999") is True

    def test_validate_student_id_invalid(self):
        """Test that invalid student IDs fail validation."""
        assert validate_student_id("123") is False  # Too short
        assert validate_student_id("123456789") is False  # Too long
        assert validate_student_id("abcd1234") is False  # Letters
        assert validate_student_id("1234 5678") is False  # Space


class TestAddStudent:
    """Test add_student function."""

    def test_add_student_success(self, app, db, service):
        """Test adding a student successfully."""
        with app.app_context():
            student = service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Computer Science",
            )

            assert student is not None
            assert student.id is not None
            assert student.first_name == "Max"
            assert student.last_name == "Mustermann"
            assert student.student_id == "12345678"
            assert student.email == "max@example.com"
            assert student.program == "Computer Science"

    def test_add_student_email_lowercase(self, app, db, service):
        """Test that email is converted to lowercase."""
        with app.app_context():
            student = service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="MAX@EXAMPLE.COM",
                program="Computer Science",
            )

            assert student.email == "max@example.com"

    def test_add_student_strips_whitespace(self, app, db, service):
        """Test that whitespace is stripped from fields."""
        with app.app_context():
            student = service.add_student(
                first_name="  Max  ",
                last_name="  Mustermann  ",
                student_id=" 12345678 ",
                email=" max@example.com ",
                program="  Computer Science  ",
            )

            assert student.first_name == "Max"
            assert student.last_name == "Mustermann"
            assert student.student_id == "12345678"
            assert student.email == "max@example.com"
            assert student.program == "Computer Science"

    def test_add_student_empty_first_name(self, app, db, service):
        """Test that empty first name raises ValueError."""
        with app.app_context():
            import pytest

            with pytest.raises(ValueError, match="First name cannot be empty"):
                service.add_student(
                    first_name="",
                    last_name="Mustermann",
                    student_id="12345678",
                    email="max@example.com",
                    program="Computer Science",
                )

    def test_add_student_empty_last_name(self, app, db, service):
        """Test that empty last name raises ValueError."""
        with app.app_context():
            import pytest

            with pytest.raises(ValueError, match="Last name cannot be empty"):
                service.add_student(
                    first_name="Max",
                    last_name="",
                    student_id="12345678",
                    email="max@example.com",
                    program="Computer Science",
                )

    def test_add_student_invalid_student_id(self, app, db, service):
        """Test that invalid student ID raises ValueError."""
        with app.app_context():
            import pytest

            with pytest.raises(ValueError, match="Invalid student ID format"):
                service.add_student(
                    first_name="Max",
                    last_name="Mustermann",
                    student_id="123",
                    email="max@example.com",
                    program="Computer Science",
                )

    def test_add_student_invalid_email(self, app, db, service):
        """Test that invalid email raises ValueError."""
        with app.app_context():
            import pytest

            with pytest.raises(ValueError, match="Invalid email format"):
                service.add_student(
                    first_name="Max",
                    last_name="Mustermann",
                    student_id="12345678",
                    email="invalid-email",
                    program="Computer Science",
                )

    def test_add_student_empty_program(self, app, db, service):
        """Test that empty program raises ValueError."""
        with app.app_context():
            import pytest

            with pytest.raises(ValueError, match="Program cannot be empty"):
                service.add_student(
                    first_name="Max",
                    last_name="Mustermann",
                    student_id="12345678",
                    email="max@example.com",
                    program="",
                )

    def test_add_student_duplicate_student_id(self, app, db, service):
        """Test that duplicate student ID raises ValueError."""
        with app.app_context():
            import pytest

            service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Computer Science",
            )

            with pytest.raises(ValueError, match="already exists"):
                service.add_student(
                    first_name="Anna",
                    last_name="Schmidt",
                    student_id="12345678",
                    email="anna@example.com",
                    program="Mathematics",
                )

    def test_add_student_duplicate_email(self, app, db, service):
        """Test that duplicate email raises ValueError."""
        with app.app_context():
            import pytest

            service.add_student(
                first_name="Max",
                last_name="Mustermann",
                student_id="12345678",
                email="max@example.com",
                program="Computer Science",
            )

            with pytest.raises(ValueError, match="already exists"):
                service.add_student(
                    first_name="Anna",
                    last_name="Schmidt",
                    student_id="87654321",
                    email="max@example.com",
                    program="Mathematics",
                )


class TestListStudents:
    """Test list_students function."""

    def test_list_students_empty(self, app, db, service):
        """Test listing students when none exist."""
        with app.app_context():
            students = service.list_students()
            assert students == []

    def test_list_students_multiple(self, app, db, service):
        """Test listing multiple students."""
        with app.app_context():
            service.add_student("Max", "Mustermann", "12345678", "max@example.com", "CS")
            service.add_student("Anna", "Schmidt", "87654321", "anna@example.com", "Math")
            service.add_student("Tom", "Müller", "11111111", "tom@example.com", "CS")

            students = service.list_students()
            assert len(students) == 3

            # Check alphabetical ordering by last name
            names = [f"{s.last_name}, {s.first_name}" for s in students]
            assert names == sorted(names)

    def test_list_students_search_by_name(self, app, db, service):
        """Test searching students by name."""
        with app.app_context():
            service.add_student("Max", "Mustermann", "12345678", "max@example.com", "CS")
            service.add_student("Anna", "Schmidt", "87654321", "anna@example.com", "Math")
            service.add_student("Maria", "Müller", "11111111", "maria@example.com", "CS")

            students = service.list_students(search="Max")
            assert len(students) == 1
            assert students[0].first_name == "Max"

    def test_list_students_search_by_student_id(self, app, db, service):
        """Test searching students by student ID."""
        with app.app_context():
            service.add_student("Max", "Mustermann", "12345678", "max@example.com", "CS")
            service.add_student("Anna", "Schmidt", "87654321", "anna@example.com", "Math")

            students = service.list_students(search="87654321")
            assert len(students) == 1
            assert students[0].student_id == "87654321"

    def test_list_students_search_by_email(self, app, db, service):
        """Test searching students by email."""
        with app.app_context():
            service.add_student("Max", "Mustermann", "12345678", "max@example.com", "CS")
            service.add_student("Anna", "Schmidt", "87654321", "anna@example.com", "Math")

            students = service.list_students(search="anna")
            assert len(students) == 1
            assert students[0].email == "anna@example.com"

    def test_list_students_filter_by_program(self, app, db, service):
        """Test filtering students by program."""
        with app.app_context():
            service.add_student("Max", "Mustermann", "12345678", "max@example.com", "CS")
            service.add_student("Anna", "Schmidt", "87654321", "anna@example.com", "Math")
            service.add_student("Tom", "Müller", "11111111", "tom@example.com", "CS")

            students = service.list_students(program="CS")
            assert len(students) == 2

            students = service.list_students(program="Math")
            assert len(students) == 1


class TestGetStudent:
    """Test get_student and get_student_by_student_id functions."""

    def test_get_student_exists(self, app, db, service):
        """Test getting an existing student by database ID."""
        with app.app_context():
            created = service.add_student(
                "Max", "Mustermann", "12345678", "max@example.com", "CS"
            )
            student = service.get_student(created.id)

            assert student is not None
            assert student.id == created.id
            assert student.first_name == "Max"

    def test_get_student_not_found(self, app, db, service):
        """Test getting a non-existent student."""
        with app.app_context():
            student = service.get_student(999)
            assert student is None

    def test_get_student_by_student_id_exists(self, app, db, service):
        """Test getting a student by student ID."""
        with app.app_context():
            service.add_student("Max", "Mustermann", "12345678", "max@example.com", "CS")
            student = service.get_student_by_student_id("12345678")

            assert student is not None
            assert student.student_id == "12345678"
            assert student.first_name == "Max"

    def test_get_student_by_student_id_not_found(self, app, db, service):
        """Test getting a non-existent student by student ID."""
        with app.app_context():
            student = service.get_student_by_student_id("99999999")
            assert student is None


class TestUpdateStudent:
    """Test update_student function."""

    def test_update_student_first_name(self, app, db, service):
        """Test updating student's first name."""
        with app.app_context():
            created = service.add_student(
                "Max", "Mustermann", "12345678", "max@example.com", "CS"
            )
            updated = service.update_student(created.id, first_name="Maximilian")

            assert updated is not None
            assert updated.first_name == "Maximilian"
            assert updated.last_name == "Mustermann"  # Unchanged

    def test_update_student_email(self, app, db, service):
        """Test updating student's email."""
        with app.app_context():
            created = service.add_student(
                "Max", "Mustermann", "12345678", "max@example.com", "CS"
            )
            updated = service.update_student(created.id, email="new@example.com")

            assert updated is not None
            assert updated.email == "new@example.com"

    def test_update_student_multiple_fields(self, app, db, service):
        """Test updating multiple fields."""
        with app.app_context():
            created = service.add_student(
                "Max", "Mustermann", "12345678", "max@example.com", "CS"
            )
            updated = service.update_student(
                created.id,
                first_name="Maximilian",
                last_name="Meyer",
                program="Mathematics",
            )

            assert updated is not None
            assert updated.first_name == "Maximilian"
            assert updated.last_name == "Meyer"
            assert updated.program == "Mathematics"

    def test_update_student_not_found(self, app, db, service):
        """Test updating non-existent student."""
        with app.app_context():
            result = service.update_student(999, first_name="Test")
            assert result is None

    def test_update_student_no_fields(self, app, db, service):
        """Test that updating without fields raises ValueError."""
        with app.app_context():
            import pytest

            created = service.add_student(
                "Max", "Mustermann", "12345678", "max@example.com", "CS"
            )

            with pytest.raises(ValueError, match="At least one field"):
                service.update_student(created.id)

    def test_update_student_invalid_email(self, app, db, service):
        """Test that invalid email raises ValueError."""
        with app.app_context():
            import pytest

            created = service.add_student(
                "Max", "Mustermann", "12345678", "max@example.com", "CS"
            )

            with pytest.raises(ValueError, match="Invalid email format"):
                service.update_student(created.id, email="invalid-email")

    def test_update_student_duplicate_email(self, app, db, service):
        """Test that duplicate email raises ValueError."""
        with app.app_context():
            import pytest

            service.add_student("Max", "Mustermann", "12345678", "max@example.com", "CS")
            student2 = service.add_student(
                "Anna", "Schmidt", "87654321", "anna@example.com", "Math"
            )

            with pytest.raises(ValueError, match="already exists"):
                service.update_student(student2.id, email="max@example.com")


class TestDeleteStudent:
    """Test delete_student function."""

    def test_delete_student_success(self, app, db, service):
        """Test deleting a student successfully."""
        with app.app_context():
            created = service.add_student(
                "Max", "Mustermann", "12345678", "max@example.com", "CS"
            )
            result = service.delete_student(created.id)

            assert result is True

            # Verify it's deleted
            student = service.get_student(created.id)
            assert student is None

    def test_delete_student_not_found(self, app, db, service):
        """Test deleting non-existent student."""
        with app.app_context():
            result = service.delete_student(999)
            assert result is False
