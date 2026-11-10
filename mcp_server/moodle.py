"""
Moodle MCP Server.

Provides Claude Code tools to interact with a Moodle LMS instance
via its classic Web Services REST API (/webservice/rest/server.php).

Configuration (environment variables):
  MOODLE_URL    Base URL of the Moodle instance, e.g. https://moodle.jv0.me
  MOODLE_TOKEN  API token from Site Admin → Server → Web Services → Tokens

Usage:
  uv run python mcp_server/moodle.py
"""

import os

import httpx
from fastmcp import FastMCP

BASE_URL = os.environ.get("MOODLE_URL", "").rstrip("/")
TOKEN = os.environ.get("MOODLE_TOKEN", "")

mcp = FastMCP("moodle")

WS = "/webservice/rest/server.php"


def _ws(function: str, **params: str | int | float) -> dict[str, object] | list[object]:
    """Call a Moodle Web Service function and return parsed JSON."""
    url = f"{BASE_URL}{WS}"
    data = {
        "wstoken": TOKEN,
        "wsfunction": function,
        "moodlewsrestformat": "json",
        **{k: str(v) for k, v in params.items()},
    }
    try:
        resp = httpx.post(url, data=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if isinstance(result, dict) and "exception" in result:
            return {"error": f"{result.get('errorcode')}: {result.get('message')}"}
        return result
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


def _wrap(data: dict | list) -> dict:
    """Ensure tools always return a dict (fastmcp requirement)."""
    if isinstance(data, list):
        return {"items": data, "count": len(data)}
    return data  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Info & connection
# ---------------------------------------------------------------------------


@mcp.tool()
def moodle_site_info() -> dict:
    """Return site name, Moodle version, and the authenticated user's name."""
    return _wrap(_ws("core_webservice_get_site_info"))


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------


@mcp.tool()
def moodle_list_my_courses() -> dict:
    """
    List all courses the authenticated user (token owner) is enrolled in.
    Includes course id, shortname, fullname, and category.
    """
    info = _ws("core_webservice_get_site_info")
    if isinstance(info, dict) and "error" in info:
        return info
    user_id = 0
    if isinstance(info, dict):
        uid = info.get("userid", 0)
        if isinstance(uid, (int, float)):
            user_id = int(uid)
    return _wrap(_ws("core_enrol_get_users_courses", userid=user_id))


@mcp.tool()
def moodle_get_course_contents(course_id: int) -> dict:
    """
    Return the sections and modules (topics, files, assignments, …) of a course.

    Args:
        course_id: Moodle course id (from moodle_list_my_courses)
    """
    return _wrap(_ws("core_course_get_contents", courseid=course_id))


@mcp.tool()
def moodle_list_participants(course_id: int) -> dict:
    """
    List all users enrolled in a course.

    Args:
        course_id: Moodle course id
    """
    return _wrap(_ws("core_enrol_get_enrolled_users", courseid=course_id))


@mcp.tool()
def moodle_search_users(query: str) -> dict:
    """
    Search for Moodle users by name or email.

    Args:
        query: Search string (matched against firstname, lastname, email)
    """
    search_params: dict[str, str | int | float] = {
        "criteria[0][key]": "fullname",
        "criteria[0][value]": f"%{query}%",
    }
    return _wrap(_ws("core_user_get_users", **search_params))


@mcp.tool()
def moodle_create_course(
    fullname: str,
    shortname: str,
    category_id: int = 1,
    summary: str = "",
) -> dict:
    """
    Create a new course in Moodle.

    Args:
        fullname: Full course name, e.g. 'Methodikseminar MedienProjekte WiSe 2026'
        shortname: Short unique name, e.g. 'EHMM-WS26'
        category_id: Category id (default 1 = top-level)
        summary: Optional course description (HTML allowed)
    """
    course_params: dict[str, str | int | float] = {
        "courses[0][fullname]": fullname,
        "courses[0][shortname]": shortname,
        "courses[0][categoryid]": category_id,
        "courses[0][summary]": summary,
        "courses[0][summaryformat]": 1,
    }
    return _wrap(_ws("core_course_create_courses", **course_params))


@mcp.tool()
def moodle_enrol_user(user_id: int, course_id: int, role_id: int = 5) -> dict:
    """
    Enrol a user in a course (manual enrolment).

    Args:
        user_id: Moodle user id (from moodle_search_users or moodle_list_participants)
        course_id: Moodle course id
        role_id: Role id — 5 = Teilnehmer/in (Student), 3 = Lehrer/in (default: 5)
    """
    enrol_params: dict[str, str | int | float] = {
        "enrolments[0][roleid]": role_id,
        "enrolments[0][userid]": user_id,
        "enrolments[0][courseid]": course_id,
    }
    return _wrap(_ws("enrol_manual_enrol_users", **enrol_params))


@mcp.tool()
def moodle_get_assignments(course_id: int) -> dict:
    """
    List all assignments in a course.

    Args:
        course_id: Moodle course id
    """
    return _wrap(
        _ws(
            "mod_assign_get_assignments",
            **{"courseids[0]": course_id},
        )
    )


@mcp.tool()
def moodle_get_grades(course_id: int, user_id: int = 0) -> dict:
    """
    Return grades for a course. Optionally filter by user.

    Args:
        course_id: Moodle course id
        user_id: Optional Moodle user id (0 = all users)
    """
    params: dict[str, str | int] = {"courseid": course_id}
    if user_id:
        params["userid"] = user_id
    return _wrap(_ws("core_grades_get_grades", **params))


if __name__ == "__main__":
    mcp.run()
