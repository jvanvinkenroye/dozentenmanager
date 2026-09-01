"""
REST API routes blueprint.

This module provides JSON API endpoints for accessing and modifying system data.
GET endpoints use session-based auth (Flask-Login).
Write endpoints use API-key auth (X-API-Key header).
"""

import hashlib
import logging
import os
from functools import wraps
from typing import Any

import openpyxl
from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService
from app.services.grade_service import GradeService
from app.services.student_service import StudentService
from app.services.university_service import UniversityService

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("api", __name__, url_prefix="/api")


def _get_api_key() -> str | None:
    return os.environ.get("DOZENTENMANAGER_API_KEY")


def require_api_key(f):  # type: ignore[no-untyped-def]
    """Decorator: require valid X-API-Key header."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        key = _get_api_key()
        if not key:
            return jsonify({"error": "API key not configured on server"}), 500
        if request.headers.get("X-API-Key") != key:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated


def _email_to_student_id(email: str) -> str:
    """Derive a deterministic 8-digit student ID from an email address."""
    h = int(hashlib.md5(email.lower().encode(), usedforsecurity=False).hexdigest(), 16)  # noqa: S324
    return str(h % 90000000 + 10000000)


# ---------------------------------------------------------------------------
# Read endpoints (session auth)
# ---------------------------------------------------------------------------


@bp.route("/students")
@login_required
def list_students() -> Any:
    """List all students. Query params: search, program."""
    search = request.args.get("search")
    program = request.args.get("program")
    service = StudentService()
    students = service.list_students(search=search, program=program)
    return jsonify([s.to_dict() for s in students])


@bp.route("/students/<int:student_id>")
@login_required
def get_student(student_id: int) -> Any:
    """Get a single student by DB id."""
    service = StudentService()
    student = service.get_student(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student.to_dict())


@bp.route("/courses")
@login_required
def list_courses() -> Any:
    """List all courses. Query params: university_id, semester."""
    university_id = request.args.get("university_id", type=int)
    semester = request.args.get("semester")
    service = CourseService()
    courses = service.list_courses(university_id=university_id, semester=semester)
    return jsonify([c.to_dict() for c in courses])


@bp.route("/courses/<int:course_id>")
@login_required
def get_course(course_id: int) -> Any:
    """Get a single course by DB id."""
    service = CourseService()
    course = service.get_course(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(course.to_dict())


@bp.route("/grades")
@login_required
def list_grades() -> Any:
    """List grades. Query params: enrollment_id, exam_id, course_id, is_final."""
    enrollment_id = request.args.get("enrollment_id", type=int)
    exam_id = request.args.get("exam_id", type=int)
    course_id = request.args.get("course_id", type=int)
    is_final_param = request.args.get("is_final")
    is_final: bool | None = None
    if is_final_param:
        is_final = is_final_param.lower() == "true"
    service = GradeService()
    grades = service.list_grades(
        enrollment_id=enrollment_id,
        exam_id=exam_id,
        course_id=course_id,
        is_final=is_final,
    )
    return jsonify([g.to_dict() for g in grades])


@bp.route("/universities")
@login_required
def list_universities() -> Any:
    """List all universities."""
    service = UniversityService()
    universities = service.list_universities()
    return jsonify([u.to_dict() for u in universities])


# ---------------------------------------------------------------------------
# Write endpoints (API-key auth)
# ---------------------------------------------------------------------------


@bp.route("/students", methods=["POST"])
@require_api_key
def create_student() -> Any:
    """
    Create a student.

    JSON body: first_name, last_name, student_id (Matrikelnummer), email, program
    """
    data = request.get_json(force=True) or {}
    required = ["first_name", "last_name", "student_id", "email", "program"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    try:
        service = StudentService()
        student = service.add_student(
            first_name=data["first_name"],
            last_name=data["last_name"],
            student_id=str(data["student_id"]),
            email=data["email"],
            program=data["program"],
        )
        return jsonify(student.to_dict()), 201
    except (ValueError, IntegrityError) as e:
        return jsonify({"error": str(e)}), 409
    except SQLAlchemyError as e:
        logger.error("DB error creating student: %s", e)
        return jsonify({"error": "Database error"}), 500


@bp.route("/courses", methods=["POST"])
@require_api_key
def create_course() -> Any:
    """
    Create a course.

    JSON body: name, semester (YYYY_SoSe / YYYY_WiSe), university_id, slug (optional)
    """
    data = request.get_json(force=True) or {}
    required = ["name", "semester", "university_id"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    try:
        service = CourseService()
        course = service.add_course(
            name=data["name"],
            semester=data["semester"],
            university_id=int(data["university_id"]),
            slug=data.get("slug"),
        )
        return jsonify(course.to_dict()), 201
    except (ValueError, IntegrityError) as e:
        return jsonify({"error": str(e)}), 409
    except SQLAlchemyError as e:
        logger.error("DB error creating course: %s", e)
        return jsonify({"error": "Database error"}), 500


@bp.route("/enrollments", methods=["POST"])
@require_api_key
def create_enrollment() -> Any:
    """
    Enroll a student in a course.

    JSON body: student_id (Matrikelnummer string), course_id
    """
    data = request.get_json(force=True) or {}
    if not data.get("student_id") or not data.get("course_id"):
        return jsonify({"error": "Missing fields: student_id, course_id"}), 400
    try:
        service = EnrollmentService()
        enrollment = service.add_enrollment(
            student_id_str=str(data["student_id"]),
            course_id=int(data["course_id"]),
        )
        return jsonify(enrollment.to_dict()), 201
    except (ValueError, IntegrityError) as e:
        return jsonify({"error": str(e)}), 409
    except SQLAlchemyError as e:
        logger.error("DB error creating enrollment: %s", e)
        return jsonify({"error": "Database error"}), 500


@bp.route("/import/teilnehmerliste", methods=["POST"])
@require_api_key
def import_teilnehmerliste() -> Any:
    """
    Import an ILIAS Teilnehmerliste (Excel).

    Multipart form fields:
      - file: the .xlsx file
      - course_name: full course name
      - semester: e.g. 2026_SoSe
      - university_id: integer
      - slug: optional course slug

    File format (ILIAS export):
      Row 1: title (ignored)
      Row 2: empty (ignored)
      Row 3: headers — Name, E-Mail, Status (ignored)
      Rows 4+: Nachname, Vorname | email | status
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    course_name = request.form.get("course_name", "").strip()
    semester = request.form.get("semester", "").strip()
    university_id_str = request.form.get("university_id", "").strip()
    slug = request.form.get("slug") or None

    if not course_name or not semester or not university_id_str:
        return jsonify(
            {"error": "Missing form fields: course_name, semester, university_id"}
        ), 400

    try:
        university_id = int(university_id_str)
    except ValueError:
        return jsonify({"error": "university_id must be an integer"}), 400

    # Parse Excel
    try:
        wb = openpyxl.load_workbook(file, read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
    except Exception as e:
        return jsonify({"error": f"Cannot read Excel file: {e}"}), 400

    # Rows 0=title, 1=empty, 2=header — data starts at index 3
    data_rows = [
        (str(r[0]).strip(), str(r[1]).strip())
        for r in rows[3:]
        if r[0] and r[1] and "@" in str(r[1])
    ]

    if not data_rows:
        return jsonify({"error": "No valid data rows found in file"}), 400

    # Create or fetch course
    cs = CourseService()
    try:
        course = cs.add_course(
            name=course_name,
            semester=semester,
            university_id=university_id,
            slug=slug,
        )
        course_created = True
    except IntegrityError:
        # Course already exists — find it by slug or name+semester+uni
        from app.models.course import Course, generate_slug

        effective_slug = slug or generate_slug(course_name)
        course = (
            Course.query.filter_by(
                slug=effective_slug,
                semester=semester,
                university_id=university_id,
            ).first()
            or Course.query.filter_by(
                name=course_name,
                semester=semester,
                university_id=university_id,
            ).first()
        )
        if not course:
            return jsonify(
                {"error": "Course already exists but could not be found"}
            ), 409
        course_created = False

    ss = StudentService()
    es = EnrollmentService()
    results: list[dict] = []

    for name_raw, email in data_rows:
        if "," in name_raw:
            last, first = name_raw.split(",", 1)
            last, first = last.strip(), first.strip()
        else:
            parts = name_raw.split()
            last, first = (
                (parts[-1], " ".join(parts[:-1])) if len(parts) > 1 else (name_raw, "")
            )

        student_id = _email_to_student_id(email)

        from app.models.student import Student

        existing = Student.query.filter_by(email=email).first()
        student_created = False
        if not existing:
            try:
                ss.add_student(
                    first_name=first,
                    last_name=last,
                    student_id=student_id,
                    email=email,
                    program="",
                )
                student_created = True
            except Exception as e:
                results.append({"email": email, "status": "error", "detail": str(e)})
                continue
        else:
            student_id = existing.student_id

        enrolled = False
        try:
            es.add_enrollment(student_id_str=student_id, course_id=int(course.id))
            enrolled = True
        except IntegrityError:
            pass  # already enrolled
        except Exception as e:
            results.append({"email": email, "status": "error", "detail": str(e)})
            continue

        results.append(
            {
                "email": email,
                "name": f"{first} {last}".strip(),
                "student_id": student_id,
                "student_created": student_created,
                "enrolled": enrolled,
                "status": "ok",
            }
        )

    return jsonify(
        {
            "course": {"id": course.id, "name": course.name, "created": course_created},
            "total": len(results),
            "created": sum(1 for r in results if r.get("student_created")),
            "enrolled": sum(1 for r in results if r.get("enrolled")),
            "errors": sum(1 for r in results if r.get("status") == "error"),
            "rows": results,
        }
    ), 201
