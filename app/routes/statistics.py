"""Statistics routes for grade analysis and reporting."""

from flask import Blueprint, render_template
from flask_login import login_required

from app.services.statistics_service import (
    get_course_stats,
    get_global_stats,
    get_student_stats,
)

bp = Blueprint("statistics", __name__, url_prefix="/statistics")


@bp.route("/")
@login_required
def index():
    stats = get_global_stats()
    return render_template("statistics/index.html", stats=stats)


@bp.route("/course/<int:course_id>")
@login_required
def course(course_id: int):
    stats = get_course_stats(course_id, include_exams=True)
    if stats is None:
        from flask import abort

        abort(404)
    return render_template("statistics/course.html", stats=stats)


@bp.route("/student/<int:student_id>")
@login_required
def student(student_id: int):
    stats = get_student_stats(student_id)
    if stats is None:
        from flask import abort

        abort(404)
    return render_template("statistics/student.html", stats=stats)
