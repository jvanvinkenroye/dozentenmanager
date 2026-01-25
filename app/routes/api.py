"""
REST API routes blueprint.

This module provides JSON API endpoints for accessing system data.
"""

from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.services.course_service import CourseService
from app.services.grade_service import GradeService
from app.services.student_service import StudentService

# Create blueprint
bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/students")
@login_required
def list_students() -> Any:
    """
    List all students.
    
    Query parameters:
        search: Optional search term
        program: Optional program filter
    """
    search = request.args.get("search")
    program = request.args.get("program")
    
    service = StudentService()
    students = service.list_students(search=search, program=program)
    
    return jsonify([student.to_dict() for student in students])


@bp.route("/students/<int:student_id>")
@login_required
def get_student(student_id: int) -> Any:
    """Get a single student by ID."""
    service = StudentService()
    student = service.get_student(student_id)
    
    if not student:
        return jsonify({"error": "Student not found"}), 404
        
    return jsonify(student.to_dict())


@bp.route("/courses")
@login_required
def list_courses() -> Any:
    """
    List all courses.
    
    Query parameters:
        university_id: Optional university filter
        semester: Optional semester filter
    """
    university_id = request.args.get("university_id", type=int)
    semester = request.args.get("semester")
    
    service = CourseService()
    courses = service.list_courses(university_id=university_id, semester=semester)
    
    return jsonify([course.to_dict() for course in courses])


@bp.route("/courses/<int:course_id>")
@login_required
def get_course(course_id: int) -> Any:
    """Get a single course by ID."""
    service = CourseService()
    course = service.get_course(course_id)
    
    if not course:
        return jsonify({"error": "Course not found"}), 404
        
    return jsonify(course.to_dict())


@bp.route("/grades")
@login_required
def list_grades() -> Any:
    """
    List grades with filters.
    
    Query parameters:
        enrollment_id: Optional enrollment filter
        exam_id: Optional exam filter
        course_id: Optional course filter
        is_final: Optional final status filter (true/false)
    """
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
        is_final=is_final
    )
    
    return jsonify([grade.to_dict() for grade in grades])
