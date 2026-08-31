"""
Grade management routes for Dozentenmanager.

This module provides Flask routes for managing grades, exam components,
and viewing grade statistics/analytics.
"""

import logging
import os
from pathlib import Path
from typing import cast

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required
from sqlalchemy import func
from werkzeug.datastructures import FileStorage

from app import db
from app.forms.grade import (
    BulkGradeForm,
    ExamComponentForm,
    GradeFilterForm,
    GradeForm,
)
from app.forms.import_forms import GradeImportForm
from app.models import (
    Course,
    Enrollment,
    Exam,
    ExamComponent,
    Grade,
    Student,
)
from app.models.grade import (
    calculate_percentage,
    percentage_to_german_grade,
)
from app.services.grade_service import GradeService
from app.services.student_service import StudentService
from app.utils.auth import admin_required
from app.utils.import_utils import (
    load_import_headers,
    load_import_rows,
    save_import_file,
)

GRADE_IMPORT_HEADERS = ["student_id", "points"]

logger = logging.getLogger(__name__)

bp = Blueprint("grade", __name__, url_prefix="/grades")


@bp.route("/")
@login_required
def index():
    """List all grades with filtering options."""
    form = GradeFilterForm(request.args)

    # Populate filter dropdowns
    courses = Course.query.order_by(Course.name).all()
    form.course_id.choices = [(0, "Alle Kurse")] + [
        (int(c.id), f"{c.name} ({c.semester})") for c in courses
    ]  # type: ignore

    exams = Exam.query.order_by(Exam.exam_date.desc()).all()
    form.exam_id.choices = [(0, "Alle Prüfungen")] + [
        (int(e.id), f"{e.name} - {e.exam_date}") for e in exams
    ]  # type: ignore

    students = (
        Student.query.filter(Student.deleted_at.is_(None))
        .order_by(Student.last_name, Student.first_name)
        .all()
    )
    form.student_id.choices = [(0, "Alle Studierenden")] + [
        (int(s.id), f"{s.last_name}, {s.first_name} ({s.student_id})") for s in students
    ]  # type: ignore

    # Build query
    query = (
        Grade.query.join(Enrollment).join(Student).filter(Student.deleted_at.is_(None))
    )

    # Apply filters
    course_id = request.args.get("course_id", type=int)
    if course_id:
        query = query.join(Exam).filter(Exam.course_id == course_id)

    exam_id = request.args.get("exam_id", type=int)
    if exam_id:
        query = query.filter(Grade.exam_id == exam_id)

    student_id = request.args.get("student_id", type=int)
    if student_id:
        query = query.filter(Enrollment.student_id == student_id)

    is_final = request.args.get("is_final")
    if is_final == "1":
        query = query.filter(Grade.is_final == True)  # noqa: E712
    elif is_final == "0":
        query = query.filter(Grade.is_final == False)  # noqa: E712

    # Execute query with pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    grades = query.order_by(Grade.graded_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "grade/list.html",
        grades=grades,
        form=form,
        course_id=course_id,
        exam_id=exam_id,
        student_id=student_id,
        is_final=is_final,
    )


@bp.route("/<int:grade_id>")
@login_required
def show(grade_id: int):
    """Show grade details."""
    grade = Grade.query.get_or_404(grade_id)
    return render_template("grade/detail.html", grade=grade)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Add a new grade."""
    form = GradeForm()

    # Populate dropdowns
    enrollments = (
        Enrollment.query.join(Student)
        .join(Course)
        .filter(Enrollment.status == "active")
        .order_by(Student.last_name, Student.first_name)
        .all()
    )
    form.enrollment_id.choices = [
        (
            e.id,
            f"{e.student.last_name}, {e.student.first_name} "
            f"({e.student.student_id}) - {e.course.name}",
        )
        for e in enrollments
    ]

    exams = Exam.query.order_by(Exam.exam_date.desc()).all()
    form.exam_id.choices = [(e.id, f"{e.name} ({e.exam_date})") for e in exams]

    # Component choices are populated via JavaScript based on exam selection
    form.component_id.choices = [(0, "--- Keine Komponente ---")]

    if form.validate_on_submit():
        service = GradeService()
        try:
            component_id = (
                form.component_id.data if form.component_id.data != 0 else None
            )

            grade = service.add_grade(
                enrollment_id=cast(int, form.enrollment_id.data),
                exam_id=cast(int, form.exam_id.data),
                points=cast(float, form.points.data),
                component_id=component_id,
                graded_by=form.graded_by.data,
                is_final=form.is_final.data,
                notes=form.notes.data,
            )

            if grade:
                flash(
                    f"Note erfolgreich hinzugefügt: {grade.grade_value} ({grade.grade_label})",
                    "success",
                )
                return redirect(url_for("grade.show", grade_id=grade.id))
            flash("Fehler beim Hinzufügen der Note", "danger")

        except ValueError as e:
            flash(f"Fehler: {e}", "danger")

    return render_template("grade/new.html", form=form)


@bp.route("/<int:grade_id>/edit", methods=["GET", "POST"])
@login_required
def edit(grade_id: int):
    """Edit an existing grade."""
    grade = Grade.query.get_or_404(grade_id)
    form = GradeForm(obj=grade)

    # Populate dropdowns (disabled since we can't change enrollment/exam)
    form.enrollment_id.choices = [
        (
            grade.enrollment_id,
            f"{grade.enrollment.student.last_name}, {grade.enrollment.student.first_name}",
        )
    ]
    form.exam_id.choices = [(grade.exam_id, grade.exam.name)]
    form.component_id.choices = [(0, "--- Keine Komponente ---")]
    if grade.component_id:
        form.component_id.choices.append((grade.component_id, grade.component.name))

    if form.validate_on_submit():
        service = GradeService()
        try:
            updated = service.update_grade(
                grade_id=grade_id,
                points=form.points.data,
                is_final=form.is_final.data,
                notes=form.notes.data,
                graded_by=form.graded_by.data,
            )

            if updated:
                flash("Note erfolgreich aktualisiert", "success")
                return redirect(url_for("grade.show", grade_id=grade_id))
            flash("Fehler beim Aktualisieren der Note", "danger")

        except ValueError as e:
            flash(f"Fehler: {e}", "danger")

    return render_template("grade/edit.html", form=form, grade=grade)


@bp.route("/<int:grade_id>/delete", methods=["GET", "POST"])
@login_required
@admin_required
def delete(grade_id: int):
    """Delete a grade."""
    grade = Grade.query.get_or_404(grade_id)

    if request.method == "POST":
        service = GradeService()
        try:
            if service.delete_grade(grade_id):
                flash("Note erfolgreich gelöscht", "success")
                return redirect(url_for("grade.index"))
            flash("Fehler beim Löschen der Note", "danger")
        except ValueError as e:
            flash(f"Fehler: {e}", "danger")

    return render_template("grade/delete.html", grade=grade)


@bp.route("/bulk", methods=["GET", "POST"])
@login_required
def bulk():
    """Bulk grading interface for an exam."""
    form = BulkGradeForm()

    exams = Exam.query.order_by(Exam.exam_date.desc()).all()
    form.exam_id.choices = [(e.id, f"{e.name} ({e.exam_date})") for e in exams]
    form.component_id.choices = [(0, "--- Keine Komponente ---")]

    exam_id = request.args.get("exam_id", type=int)
    if exam_id:
        form.exam_id.data = str(exam_id)
        components = (
            ExamComponent.query.filter_by(exam_id=exam_id)
            .order_by(ExamComponent.order)
            .all()
        )
        form.component_id.choices += [
            (c.id, f"{c.name} ({c.weight}%)") for c in components
        ]

    if form.validate_on_submit():
        service = GradeService()
        exam_id = form.exam_id.data
        component_id = form.component_id.data if form.component_id.data != 0 else None
        graded_by = form.graded_by.data
        is_final = form.is_final.data

        # Process submitted grades
        success_count = 0
        error_count = 0

        for key, value in request.form.items():
            if key.startswith("points_") and value:
                enrollment_id = int(key.replace("points_", ""))
                try:
                    points = float(value)
                    grade = service.add_grade(
                        enrollment_id=enrollment_id,
                        exam_id=exam_id,
                        points=points,
                        component_id=component_id,
                        graded_by=graded_by,
                        is_final=is_final,
                    )
                    if grade:
                        success_count += 1
                    else:
                        error_count += 1
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error grading enrollment {enrollment_id}: {e}")
                    error_count += 1

        flash(
            f"{success_count} Noten erfolgreich hinzugefügt. {error_count} Fehler.",
            "success" if error_count == 0 else "warning",
        )
        return redirect(url_for("grade.index", exam_id=exam_id))

    # Get enrollments for selected exam
    enrollments = []
    max_points = 0
    if exam_id:
        exam = Exam.query.get(exam_id)
        if exam:
            enrollments = (
                Enrollment.query.join(Student)
                .filter(Enrollment.course_id == exam.course_id)
                .filter(Enrollment.status == "active")
                .order_by(Student.last_name, Student.first_name)
                .all()
            )

            component_id = request.args.get("component_id", type=int)
            if component_id:
                component = ExamComponent.query.get(component_id)
                max_points = component.max_points if component else exam.max_points
            else:
                max_points = exam.max_points

    return render_template(
        "grade/bulk.html",
        form=form,
        enrollments=enrollments,
        max_points=max_points,
        exam_id=exam_id,
    )


@bp.route("/dashboard")
@login_required
def dashboard():
    """Grade monitoring dashboard with statistics."""
    # Get overall statistics
    total_grades = Grade.query.count()
    final_grades = Grade.query.filter(Grade.is_final == True).count()  # noqa: E712

    # Get pass/fail rates
    passing = Grade.query.filter(
        Grade.is_final == True,  # noqa: E712
        Grade.grade_value <= 4.0,
    ).count()
    failing = Grade.query.filter(
        Grade.is_final == True,  # noqa: E712
        Grade.grade_value > 4.0,
    ).count()

    pass_rate = round((passing / final_grades * 100), 1) if final_grades > 0 else 0

    # Get average grade
    avg_grade = (
        db.session.query(func.avg(Grade.grade_value))
        .filter(
            Grade.is_final == True  # noqa: E712
        )
        .scalar()
        or 0
    )

    # Get grade distribution
    distribution = (
        db.session.query(Grade.grade_label, func.count(Grade.id))
        .filter(
            Grade.is_final == True  # noqa: E712
        )
        .group_by(Grade.grade_label)
        .all()
    )

    grade_distribution = {row[0]: row[1] for row in distribution}

    # Get recent exams with grades
    recent_exams = (
        db.session.query(
            Exam,
            func.count(Grade.id).label("grade_count"),
            func.avg(Grade.grade_value).label("avg_grade"),
        )
        .join(Grade, Grade.exam_id == Exam.id)
        .group_by(Exam.id)
        .order_by(Exam.exam_date.desc())
        .limit(10)
        .all()
    )

    # Get courses needing attention (low pass rates)
    course_stats = (
        db.session.query(
            Course,
            func.count(Grade.id).label("total_grades"),
            func.sum(db.case((Grade.grade_value <= 4.0, 1), else_=0)).label("passing"),
        )
        .join(Exam, Exam.course_id == Course.id)
        .join(Grade, Grade.exam_id == Exam.id)
        .filter(Grade.is_final == True)  # noqa: E712
        .group_by(Course.id)
        .all()
    )

    courses_needing_attention = [
        {
            "course": stat[0],
            "total": stat[1],
            "passing": stat[2],
            "pass_rate": round((stat[2] / stat[1] * 100), 1) if stat[1] > 0 else 0,
        }
        for stat in course_stats
        if stat[1] > 0 and (stat[2] / stat[1] * 100) < 60
    ]

    return render_template(
        "grade/dashboard.html",
        total_grades=total_grades,
        final_grades=final_grades,
        passing=passing,
        failing=failing,
        pass_rate=pass_rate,
        avg_grade=round(avg_grade, 2),
        grade_distribution=grade_distribution,
        recent_exams=recent_exams,
        courses_needing_attention=courses_needing_attention,
    )


@bp.route("/exam/<int:exam_id>/stats")
@login_required
def exam_stats(exam_id: int):
    """Show detailed statistics for an exam."""
    exam = Exam.query.get_or_404(exam_id)
    service = GradeService()
    stats = service.get_exam_statistics(exam_id)

    # Get component statistics if multi-part exam
    component_stats = []
    for component in exam.components:
        comp_grades = Grade.query.filter_by(
            exam_id=exam_id, component_id=component.id
        ).all()
        if comp_grades:
            points_list = [g.points for g in comp_grades]
            component_stats.append(
                {
                    "component": component,
                    "count": len(comp_grades),
                    "avg_points": round(sum(points_list) / len(points_list), 2),
                    "min_points": min(points_list),
                    "max_points": max(points_list),
                }
            )

    return render_template(
        "grade/exam_stats.html",
        exam=exam,
        stats=stats,
        component_stats=component_stats,
    )


@bp.route("/student/<int:student_id>")
@login_required
def student_grades(student_id: int):
    """Show all grades for a student."""
    student = (
        Student.query.filter(Student.deleted_at.is_(None))
        .filter_by(id=student_id)
        .first_or_404()
    )

    # Get all enrollments with their grades
    enrollments_with_grades = []
    for enrollment in student.enrollments:
        grades = Grade.query.filter_by(enrollment_id=enrollment.id).all()
        service = GradeService()
        weighted_avg = service.calculate_weighted_average(enrollment.id)
        enrollments_with_grades.append(
            {
                "enrollment": enrollment,
                "grades": grades,
                "weighted_average": weighted_avg,
            }
        )

    return render_template(
        "grade/student_grades.html",
        student=student,
        enrollments_with_grades=enrollments_with_grades,
    )


@bp.route("/components/<int:exam_id>")
@login_required
def components(exam_id: int):
    """Manage exam components."""
    exam = Exam.query.get_or_404(exam_id)
    service = GradeService()
    component_list = service.list_exam_components(exam_id)

    total_weight = sum(c.weight for c in component_list)

    return render_template(
        "grade/components.html",
        exam=exam,
        components=component_list,
        total_weight=total_weight,
    )


@bp.route("/components/<int:exam_id>/new", methods=["GET", "POST"])
@login_required
def new_component(exam_id: int):
    """Add a new exam component."""
    exam = Exam.query.get_or_404(exam_id)
    form = ExamComponentForm()
    form.exam_id.data = str(exam_id)

    if form.validate_on_submit():
        service = GradeService()
        try:
            component = service.add_exam_component(
                exam_id=exam_id,
                name=cast(str, form.name.data),
                weight=cast(float, form.weight.data),
                max_points=cast(float, form.max_points.data),
                order=cast(int, form.order.data) or 0,
                description=form.description.data,
            )

            if component:
                flash(
                    f"Komponente '{component.name}' erfolgreich hinzugefügt", "success"
                )
                return redirect(url_for("grade.components", exam_id=exam_id))
            flash("Fehler beim Hinzufügen der Komponente", "danger")

        except ValueError as e:
            flash(f"Fehler: {e}", "danger")

    return render_template("grade/new_component.html", form=form, exam=exam)


@bp.route("/components/<int:component_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_component(component_id: int):
    """Delete an exam component."""
    component = ExamComponent.query.get_or_404(component_id)
    exam_id = component.exam_id

    # Check for existing grades
    grade_count = Grade.query.filter_by(component_id=component_id).count()
    if grade_count > 0:
        flash(
            f"Komponente kann nicht gelöscht werden - {grade_count} Noten vorhanden",
            "danger",
        )
        return redirect(url_for("grade.components", exam_id=exam_id))

    try:
        db.session.delete(component)
        db.session.commit()
        flash("Komponente erfolgreich gelöscht", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Fehler beim Löschen: {e}", "danger")

    return redirect(url_for("grade.components", exam_id=exam_id))


@bp.route("/api/exam/<int:exam_id>/components")
@login_required
def api_exam_components(exam_id: int):
    """API endpoint to get components for an exam."""
    components = (
        ExamComponent.query.filter_by(exam_id=exam_id)
        .order_by(ExamComponent.order)
        .all()
    )

    exam = Exam.query.get(exam_id)
    max_points = exam.max_points if exam else 0

    return jsonify(
        {
            "components": [
                {
                    "id": c.id,
                    "name": c.name,
                    "weight": c.weight,
                    "max_points": c.max_points,
                }
                for c in components
            ],
            "exam_max_points": max_points,
        }
    )


@bp.route("/exam/<int:exam_id>/import-grades", methods=["GET", "POST"])
@login_required
def import_grades(exam_id: int):
    """Import grades (Matrikelnummer + Punkte) for a specific exam."""
    exam = db.session.get(Exam, exam_id)
    if not exam:
        flash("Prüfung nicht gefunden.", "error")
        return redirect(url_for("grade.index"))

    form = GradeImportForm()
    import_errors: list[str] = []
    import_summary: dict[str, int] | None = None
    mapping_headers: list[tuple[str, str]] = []
    mapping_token = ""
    mapping_format = ""
    mapping_defaults: dict[str, str] = {}
    mapping_on_duplicate = "skip"

    if request.method == "POST" and request.form.get("mapping_token"):
        mapping_token = request.form.get("mapping_token", "").strip()
        mapping_format = request.form.get("file_format", "").strip()
        mapping_on_duplicate = request.form.get("on_duplicate", "skip").strip()
        file_extension = request.form.get("file_extension", "data").strip()

        file_path = (
            Path(current_app.root_path)
            / "uploads"
            / "imports"
            / f"grades_{mapping_token}.{file_extension}"
        )
        mapping = {
            key: request.form.get(f"map_{key}", "").strip()
            for key in GRADE_IMPORT_HEADERS
        }
        mapping_defaults = mapping.copy()

        if not file_path.exists():
            flash("Importdatei nicht gefunden. Bitte erneut hochladen.", "error")
            return redirect(url_for("grade.import_grades", exam_id=exam_id))

        try:
            with file_path.open("rb") as handle:
                f = FileStorage(stream=handle, filename=file_path.name)
                mapping_headers = load_import_headers(f, mapping_format)
                handle.seek(0)
                rows = load_import_rows(
                    f, mapping_format, GRADE_IMPORT_HEADERS, mapping=mapping
                )
        except ValueError as exc:
            import_errors.append(str(exc))
            return render_template(
                "grade/import.html",
                exam=exam,
                form=form,
                import_errors=import_errors,
                mapping_headers=mapping_headers,
                mapping_token=mapping_token,
                mapping_format=mapping_format,
                mapping_defaults=mapping_defaults,
                mapping_on_duplicate=mapping_on_duplicate,
                file_extension=file_extension,
            )

        grade_service = GradeService()
        student_service = StudentService()
        created = skipped = errors = 0

        for idx, row in enumerate(rows, start=2):
            matrikelnummer = row.get("student_id", "").strip()
            if matrikelnummer.endswith(".0"):
                matrikelnummer = matrikelnummer[:-2]
            points_str = row.get("points", "").strip()
            if not matrikelnummer or not points_str:
                import_errors.append(f"Zeile {idx}: Matrikelnummer oder Punkte fehlen.")
                errors += 1
                continue

            try:
                points = float(points_str.replace(",", "."))
            except ValueError:
                import_errors.append(
                    f"Zeile {idx}: Ungültiger Punktwert '{points_str}'."
                )
                errors += 1
                continue

            student = student_service.get_student_by_student_id(matrikelnummer)
            if not student:
                import_errors.append(
                    f"Zeile {idx}: Studierender '{matrikelnummer}' nicht gefunden."
                )
                errors += 1
                continue

            enrollment = (
                db.session.query(Enrollment)
                .filter_by(student_id=student.id, course_id=exam.course_id)
                .first()
            )
            if not enrollment:
                import_errors.append(
                    f"Zeile {idx}: '{matrikelnummer}' ist nicht im Kurs eingeschrieben."
                )
                errors += 1
                continue

            existing = (
                db.session.query(Grade)
                .filter_by(enrollment_id=enrollment.id, exam_id=exam_id)
                .first()
            )
            if existing:
                if mapping_on_duplicate == "skip":
                    skipped += 1
                    continue
                if mapping_on_duplicate == "update":
                    existing.points = points
                    db.session.commit()
                    created += 1
                else:
                    import_errors.append(
                        f"Zeile {idx}: Note für '{matrikelnummer}' existiert bereits."
                    )
                    errors += 1
                continue

            try:
                grade_service.add_grade(
                    enrollment_id=enrollment.id, exam_id=exam_id, points=points
                )
                created += 1
            except ValueError as exc:
                import_errors.append(f"Zeile {idx}: {exc}")
                errors += 1

        if file_path.exists():
            try:
                os.remove(file_path)
            except OSError:
                logger.warning("Failed to remove import file %s", file_path)

        import_summary = {"created": created, "skipped": skipped, "errors": errors}
        return render_template(
            "grade/import.html",
            exam=exam,
            form=form,
            import_errors=import_errors,
            import_summary=import_summary,
        )

    if form.validate_on_submit():
        file = form.file.data
        try:
            token, file_path, extension = save_import_file(file, "grades")
            with file_path.open("rb") as handle:
                stored = FileStorage(stream=handle, filename=file_path.name)
                mapping_headers = load_import_headers(stored, form.file_format.data)
            mapping_token = token
            mapping_format = form.file_format.data
            mapping_on_duplicate = form.on_duplicate.data
            normalized = [v for v, _ in mapping_headers]
            mapping_defaults = {
                k: k if k in normalized else "" for k in GRADE_IMPORT_HEADERS
            }
            return render_template(
                "grade/import.html",
                exam=exam,
                form=form,
                import_errors=import_errors,
                mapping_headers=mapping_headers,
                mapping_token=mapping_token,
                mapping_format=mapping_format,
                mapping_defaults=mapping_defaults,
                mapping_on_duplicate=mapping_on_duplicate,
                file_extension=extension,
            )
        except ValueError as exc:
            flash(str(exc), "error")

    for _field, errs in form.errors.items():
        for err in errs:
            flash(err, "error")

    return render_template(
        "grade/import.html",
        exam=exam,
        form=form,
        import_errors=import_errors,
    )


@bp.route("/api/calculate", methods=["POST"])
@login_required
def api_calculate_grade():
    """API endpoint to calculate grade from points."""
    data = request.get_json()
    points = data.get("points", 0)
    max_points = data.get("max_points", 100)

    try:
        percentage = calculate_percentage(float(points), float(max_points))
        grade_value, grade_label = percentage_to_german_grade(percentage)

        return jsonify(
            {
                "percentage": percentage,
                "grade_value": grade_value,
                "grade_label": grade_label,
                "is_passing": grade_value <= 4.0,
            }
        )
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
