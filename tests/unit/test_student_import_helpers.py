"""
Unit tests for the student import helper functions.

These helpers parse CSV/XLSX/XLS uploads for the student import route.
They are pure functions operating on FileStorage objects, so they can be
tested without an application context.
"""

import io

import pytest
from openpyxl import Workbook
from werkzeug.datastructures import FileStorage

from app.routes.student import (
    _load_csv_rows,
    _load_import_headers,
    _load_import_rows,
    _load_xlsx_rows,
    _normalize_header,
)


def make_file(content: bytes, filename: str) -> FileStorage:
    """Wrap raw bytes in a FileStorage as Flask would receive it."""
    return FileStorage(stream=io.BytesIO(content), filename=filename)


def make_csv_file(text: str, filename: str = "students.csv") -> FileStorage:
    """Build a CSV FileStorage from a string."""
    return make_file(text.encode("utf-8"), filename)


def make_xlsx_file(
    rows: list[list[str | None]], filename: str = "students.xlsx"
) -> FileStorage:
    """Build an XLSX FileStorage from a list of rows."""
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return make_file(buffer.getvalue(), filename)


class TestNormalizeHeader:
    """Tests for _normalize_header."""

    def test_strips_and_lowercases(self):
        assert _normalize_header("  First_Name ") == "first_name"

    def test_none_and_empty_return_empty_string(self):
        assert _normalize_header(None) == ""
        assert _normalize_header("") == ""


class TestLoadCsvRows:
    """Tests for _load_csv_rows."""

    def test_parses_rows_and_normalizes_headers(self):
        file = make_csv_file(
            "First_Name,Last_Name\nMax, Mustermann \nErika,Musterfrau\n"
        )
        headers, rows = _load_csv_rows(file)
        assert headers == ["first_name", "last_name"]
        assert rows == [
            {"first_name": "Max", "last_name": "Mustermann"},
            {"first_name": "Erika", "last_name": "Musterfrau"},
        ]

    def test_handles_utf8_bom(self):
        file = make_file("first_name\nMax\n".encode("utf-8-sig"), "students.csv")
        headers, rows = _load_csv_rows(file)
        assert headers == ["first_name"]
        assert rows == [{"first_name": "Max"}]

    def test_empty_file_yields_no_rows(self):
        headers, rows = _load_csv_rows(make_csv_file(""))
        assert headers == []
        assert rows == []


class TestLoadXlsxRows:
    """Tests for _load_xlsx_rows."""

    def test_parses_rows_and_normalizes_headers(self):
        file = make_xlsx_file([["First_Name", "Last_Name"], ["Max", "Mustermann"]])
        headers, rows = _load_xlsx_rows(file)
        assert headers == ["first_name", "last_name"]
        assert rows == [{"first_name": "Max", "last_name": "Mustermann"}]

    def test_none_cells_become_empty_strings(self):
        file = make_xlsx_file([["first_name", "last_name"], ["Max", None]])
        _, rows = _load_xlsx_rows(file)
        assert rows == [{"first_name": "Max", "last_name": ""}]


class TestLoadImportHeaders:
    """Tests for _load_import_headers."""

    def test_csv_headers_keep_raw_labels(self):
        file = make_csv_file("First_Name,Last_Name\nMax,Mustermann\n")
        headers = _load_import_headers(file, "csv")
        assert headers == [("first_name", "First_Name"), ("last_name", "Last_Name")]

    def test_format_inferred_from_filename(self):
        file = make_csv_file("first_name\nMax\n")
        headers = _load_import_headers(file, None)
        assert headers == [("first_name", "first_name")]

    def test_xlsx_headers(self):
        file = make_xlsx_file([["Email", "Program"], ["a@b.de", "CS"]])
        headers = _load_import_headers(file, "xlsx")
        assert headers == [("email", "Email"), ("program", "Program")]

    def test_empty_csv_raises(self):
        with pytest.raises(ValueError, match="no rows"):
            _load_import_headers(make_csv_file(""), "csv")

    def test_unsupported_format_raises(self):
        file = make_file(b"data", "students.docx")
        with pytest.raises(ValueError, match="Unsupported format"):
            _load_import_headers(file, None)


VALID_CSV = (
    "first_name,last_name,student_id,email,program\n"
    "Max,Mustermann,12345678,max@example.com,CS\n"
)


class TestLoadImportRows:
    """Tests for _load_import_rows."""

    def test_valid_csv_without_mapping(self):
        rows = _load_import_rows(make_csv_file(VALID_CSV), "csv")
        assert rows == [
            {
                "first_name": "Max",
                "last_name": "Mustermann",
                "student_id": "12345678",
                "email": "max@example.com",
                "program": "CS",
            }
        ]

    def test_missing_required_headers_raises(self):
        file = make_csv_file("first_name,last_name\nMax,Mustermann\n")
        with pytest.raises(ValueError, match="Missing required headers"):
            _load_import_rows(file, "csv")

    def test_unsupported_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            _load_import_rows(make_file(b"x", "students.txt"), None)

    def test_mapping_renames_columns(self):
        file = make_csv_file(
            "vorname,nachname,matrikel,mail,studiengang\n"
            "Max,Mustermann,12345678,max@example.com,CS\n"
        )
        mapping = {
            "first_name": "vorname",
            "last_name": "nachname",
            "student_id": "matrikel",
            "email": "mail",
            "program": "studiengang",
        }
        rows = _load_import_rows(file, "csv", mapping=mapping)
        assert rows[0]["first_name"] == "Max"
        assert rows[0]["student_id"] == "12345678"

    def test_mapping_missing_key_raises(self):
        mapping = {
            "first_name": "first_name",
            "last_name": "last_name",
            "student_id": "",
            "email": "email",
            "program": "program",
        }
        with pytest.raises(ValueError, match="Mapping missing for: student_id"):
            _load_import_rows(make_csv_file(VALID_CSV), "csv", mapping=mapping)

    def test_mapping_duplicate_columns_raises(self):
        mapping = {
            "first_name": "first_name",
            "last_name": "first_name",
            "student_id": "student_id",
            "email": "email",
            "program": "program",
        }
        with pytest.raises(ValueError, match="duplicate column selections"):
            _load_import_rows(make_csv_file(VALID_CSV), "csv", mapping=mapping)

    def test_mapping_unknown_header_raises(self):
        mapping = {
            "first_name": "does_not_exist",
            "last_name": "last_name",
            "student_id": "student_id",
            "email": "email",
            "program": "program",
        }
        with pytest.raises(ValueError, match="unknown headers"):
            _load_import_rows(make_csv_file(VALID_CSV), "csv", mapping=mapping)
