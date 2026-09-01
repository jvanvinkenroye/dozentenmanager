"""
Dozentenmanager MCP Server.

Provides Claude Code tools to interact with a remote (or local) Dozentenmanager
instance via its REST API.

Configuration (environment variables):
  DOZENTENMANAGER_URL      Base URL of the instance, e.g. https://dmprod.jv0.me
  DOZENTENMANAGER_API_KEY  API key configured on the server

Usage:
  uv run python mcp_server/server.py
"""

import os
from pathlib import Path

import httpx
from fastmcp import FastMCP

BASE_URL = os.environ.get("DOZENTENMANAGER_URL", "http://localhost:5001").rstrip("/")
API_KEY = os.environ.get("DOZENTENMANAGER_API_KEY", "")

mcp = FastMCP("dozentenmanager")


def _headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY, "Accept": "application/json"}


def _api(method: str, path: str, **kwargs) -> dict:  # type: ignore[no-untyped-def]
    """Perform an API request and return parsed JSON or an error dict."""
    url = f"{BASE_URL}/api{path}"
    try:
        resp = httpx.request(method, url, headers=_headers(), timeout=30, **kwargs)
        resp.raise_for_status()
        data = resp.json()
        # fastmcp requires tools to return a dict, never a bare list
        if isinstance(data, list):
            return {"items": data, "count": len(data)}
        return data
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("error", e.response.text)
        except Exception:
            detail = e.response.text
        return {"error": f"HTTP {e.response.status_code}: {detail}"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Read tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_courses(semester: str = "", university_id: int = 0) -> dict:
    """
    List courses in the Dozentenmanager.

    Args:
        semester: Optional filter, e.g. '2026_SoSe' or '2026_WiSe'
        university_id: Optional university DB id to filter by
    """
    params: dict[str, str | int] = {}
    if semester:
        params["semester"] = semester
    if university_id:
        params["university_id"] = university_id
    return _api("GET", "/courses", params=params)


@mcp.tool()
def list_universities() -> dict:
    """List all universities configured in the Dozentenmanager."""
    return _api("GET", "/universities")


@mcp.tool()
def list_students(search: str = "") -> dict:
    """
    List students, optionally filtered by name, email, or Matrikelnummer.

    Args:
        search: Free-text search term
    """
    params = {"search": search} if search else {}
    return _api("GET", "/students", params=params)


# ---------------------------------------------------------------------------
# Write tools
# ---------------------------------------------------------------------------


@mcp.tool()
def create_university(name: str, slug: str = "") -> dict:
    """
    Create a new university.

    Args:
        name: Full name of the university (e.g. 'TH Köln')
        slug: Optional URL slug (auto-generated if omitted)
    """
    payload: dict[str, str] = {"name": name}
    if slug:
        payload["slug"] = slug
    return _api("POST", "/universities", json=payload)


@mcp.tool()
def create_course(name: str, semester: str, university_id: int, slug: str = "") -> dict:
    """
    Create a new course.

    Args:
        name: Full course name
        semester: Semester in format YYYY_SoSe or YYYY_WiSe (e.g. 2026_SoSe)
        university_id: Database id of the university (use list_universities to find it)
        slug: Optional URL slug (auto-generated if omitted)
    """
    payload: dict[str, str | int] = {
        "name": name,
        "semester": semester,
        "university_id": university_id,
    }
    if slug:
        payload["slug"] = slug
    return _api("POST", "/courses", json=payload)


@mcp.tool()
def add_enrollment(student_id: str, course_id: int) -> dict:
    """
    Enroll a student (by Matrikelnummer) in a course.

    Args:
        student_id: Matrikelnummer (8-digit string) of the student
        course_id: Database id of the course
    """
    return _api(
        "POST", "/enrollments", json={"student_id": student_id, "course_id": course_id}
    )


@mcp.tool()
def import_teilnehmerliste(
    file_path: str,
    course_name: str,
    semester: str,
    university_id: int,
    slug: str = "",
) -> dict:
    """
    Import an ILIAS Teilnehmerliste Excel file into the Dozentenmanager.

    Creates the course if it doesn't exist, then imports all students from the
    file and enrolls them in that course. Handles the ILIAS export format
    (row 1 = title, row 3 = headers Name/E-Mail/Status, rows 4+ = data).

    Existing students (matched by email) are not duplicated.
    Existing enrollments are skipped without error.

    Args:
        file_path: Absolute local path to the .xlsx file
        course_name: Full name of the course to create or find
        semester: Semester, e.g. '2026_SoSe'
        university_id: Database id of the university
        slug: Optional URL slug for the course
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    form_data: dict[str, str] = {
        "course_name": course_name,
        "semester": semester,
        "university_id": str(university_id),
    }
    if slug:
        form_data["slug"] = slug

    with path.open("rb") as f:
        files = {
            "file": (
                path.name,
                f,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        url = f"{BASE_URL}/api/import/teilnehmerliste"
        try:
            resp = httpx.post(
                url,
                headers={"X-API-Key": API_KEY},
                data=form_data,
                files=files,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("error", e.response.text)
            except Exception:
                detail = e.response.text
            return {"error": f"HTTP {e.response.status_code}: {detail}"}
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
def delete_course(course_id: int) -> dict:
    """
    Delete a course and all its enrollments, exams and grades.

    Args:
        course_id: Database id of the course to delete
    """
    return _api("DELETE", f"/courses/{course_id}")


@mcp.tool()
def delete_student(student_id: int) -> dict:
    """
    Delete a student by database id.

    Args:
        student_id: Database id of the student (NOT Matrikelnummer)
    """
    return _api("DELETE", f"/students/{student_id}")


@mcp.tool()
def delete_enrollment(student_id: str, course_id: int) -> dict:
    """
    Remove a student's enrollment from a course.

    Args:
        student_id: Matrikelnummer (8-digit string) of the student
        course_id: Database id of the course
    """
    return _api(
        "DELETE",
        "/enrollments",
        json={"student_id": student_id, "course_id": course_id},
    )


if __name__ == "__main__":
    mcp.run()
