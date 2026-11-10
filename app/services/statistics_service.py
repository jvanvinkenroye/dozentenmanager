"""Statistics service for grade analysis and reporting."""

from dataclasses import dataclass, field

from sqlalchemy import func

from app import db
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.grade import Grade
from app.models.student import Student

GRADE_LABELS = {
    1.0: "1,0",
    1.3: "1,3",
    1.7: "1,7",
    2.0: "2,0",
    2.3: "2,3",
    2.7: "2,7",
    3.0: "3,0",
    3.3: "3,3",
    3.7: "3,7",
    4.0: "4,0",
    5.0: "5,0",
}

PASSING_THRESHOLD = 4.0


@dataclass
class GradeDistribution:
    labels: list[str]
    counts: list[int]
    total: int
    passed: int
    failed: int

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return round(self.passed / self.total * 100, 1)

    @property
    def fail_rate(self) -> float:
        return round(100 - self.pass_rate, 1)


@dataclass
class ExamStats:
    exam_id: int
    exam_name: str
    total_grades: int
    average_grade: float | None
    average_percentage: float | None
    distribution: GradeDistribution


@dataclass
class CourseStats:
    course_id: int
    course_name: str
    enrollment_count: int
    graded_count: int
    average_grade: float | None
    distribution: GradeDistribution
    exam_stats: list[ExamStats] = field(default_factory=list)


@dataclass
class StudentStats:
    student_id: int
    student_name: str
    student_number: str
    grades: list[dict]
    average_grade: float | None
    average_percentage: float | None
    passed_count: int
    failed_count: int


@dataclass
class GlobalStats:
    total_students: int
    total_courses: int
    total_exams: int
    total_grades: int
    overall_average_grade: float | None
    overall_pass_rate: float
    distribution: GradeDistribution
    top_courses: list[CourseStats]


def _build_distribution(grades: list[Grade]) -> GradeDistribution:
    counts: dict[float, int] = dict.fromkeys(GRADE_LABELS, 0)
    passed = 0
    failed = 0

    for grade in grades:
        if grade.grade_value is not None:
            bucket = min(GRADE_LABELS.keys(), key=lambda k: abs(k - grade.grade_value))
            counts[bucket] += 1
            if grade.grade_value <= PASSING_THRESHOLD:
                passed += 1
            else:
                failed += 1

    return GradeDistribution(
        labels=[GRADE_LABELS[k] for k in sorted(counts)],
        counts=[counts[k] for k in sorted(counts)],
        total=passed + failed,
        passed=passed,
        failed=failed,
    )


def get_exam_stats(exam_id: int) -> ExamStats | None:
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        return None

    grades = (
        db.session.query(Grade)
        .filter(Grade.exam_id == exam_id, Grade.grade_value.isnot(None))
        .all()
    )

    avg_grade = (
        db.session.query(func.avg(Grade.grade_value))
        .filter(Grade.exam_id == exam_id, Grade.grade_value.isnot(None))
        .scalar()
    )
    avg_pct = (
        db.session.query(func.avg(Grade.percentage))
        .filter(Grade.exam_id == exam_id)
        .scalar()
    )

    return ExamStats(
        exam_id=exam_id,
        exam_name=exam.name,
        total_grades=len(grades),
        average_grade=round(float(avg_grade), 2) if avg_grade is not None else None,
        average_percentage=round(float(avg_pct), 1) if avg_pct is not None else None,
        distribution=_build_distribution(grades),
    )


def get_course_stats(course_id: int, include_exams: bool = True) -> CourseStats | None:
    from app.models.course import Course

    course = db.session.get(Course, course_id)
    if course is None:
        return None

    enrollment_count = (
        db.session.query(func.count(Enrollment.id))
        .filter(Enrollment.course_id == course_id)
        .scalar()
        or 0
    )

    grades = (
        db.session.query(Grade)
        .join(Exam, Grade.exam_id == Exam.id)
        .filter(Exam.course_id == course_id, Grade.grade_value.isnot(None))
        .all()
    )

    avg_grade = (
        db.session.query(func.avg(Grade.grade_value))
        .join(Exam, Grade.exam_id == Exam.id)
        .filter(Exam.course_id == course_id, Grade.grade_value.isnot(None))
        .scalar()
    )

    exam_stats: list[ExamStats] = []
    if include_exams:
        for exam in course.exams:
            stats = get_exam_stats(int(exam.id))
            if stats is not None:
                exam_stats.append(stats)

    return CourseStats(
        course_id=course_id,
        course_name=course.name,
        enrollment_count=int(enrollment_count),
        graded_count=len(grades),
        average_grade=round(float(avg_grade), 2) if avg_grade is not None else None,
        distribution=_build_distribution(grades),
        exam_stats=exam_stats,
    )


def get_student_stats(student_id: int) -> StudentStats | None:
    student = db.session.get(Student, student_id)
    if student is None:
        return None

    grade_rows = (
        db.session.query(Grade, Exam)
        .join(Exam, Grade.exam_id == Exam.id)
        .join(Enrollment, Grade.enrollment_id == Enrollment.id)
        .filter(Enrollment.student_id == student_id)
        .order_by(Exam.exam_date.desc())
        .all()
    )

    grades_data = []
    passed = 0
    failed = 0
    for grade, exam in grade_rows:
        grades_data.append(
            {
                "exam_name": exam.name,
                "exam_id": exam.id,
                "course_name": exam.course.name,
                "course_id": exam.course_id,
                "grade_value": grade.grade_value,
                "grade_label": grade.grade_label,
                "percentage": grade.percentage,
                "points": grade.points,
                "graded_at": grade.graded_at,
            }
        )
        if grade.grade_value is not None:
            if grade.grade_value <= PASSING_THRESHOLD:
                passed += 1
            else:
                failed += 1

    values = [g["grade_value"] for g in grades_data if g["grade_value"] is not None]
    avg_grade = round(sum(values) / len(values), 2) if values else None

    pcts = [g["percentage"] for g in grades_data if g["percentage"] is not None]
    avg_pct = round(sum(pcts) / len(pcts), 1) if pcts else None

    return StudentStats(
        student_id=student_id,
        student_name=f"{student.first_name} {student.last_name}",
        student_number=student.student_id,
        grades=grades_data,
        average_grade=avg_grade,
        average_percentage=avg_pct,
        passed_count=passed,
        failed_count=failed,
    )


def get_global_stats() -> GlobalStats:
    from app.models.course import Course

    total_students = db.session.query(func.count(Student.id)).scalar() or 0
    total_courses = db.session.query(func.count(Course.id)).scalar() or 0
    total_exams = db.session.query(func.count(Exam.id)).scalar() or 0
    total_grades = db.session.query(func.count(Grade.id)).scalar() or 0

    all_grades = db.session.query(Grade).filter(Grade.grade_value.isnot(None)).all()

    avg_grade = (
        db.session.query(func.avg(Grade.grade_value))
        .filter(Grade.grade_value.isnot(None))
        .scalar()
    )

    distribution = _build_distribution(all_grades)

    # Top 5 courses by enrollment count
    top_course_ids = (
        db.session.query(Enrollment.course_id, func.count(Enrollment.id).label("cnt"))
        .group_by(Enrollment.course_id)
        .order_by(func.count(Enrollment.id).desc())
        .limit(5)
        .all()
    )
    top_courses = []
    for course_id, _ in top_course_ids:
        stats = get_course_stats(int(course_id), include_exams=False)
        if stats:
            top_courses.append(stats)

    return GlobalStats(
        total_students=int(total_students),
        total_courses=int(total_courses),
        total_exams=int(total_exams),
        total_grades=int(total_grades),
        overall_average_grade=round(float(avg_grade), 2) if avg_grade else None,
        overall_pass_rate=distribution.pass_rate,
        distribution=distribution,
        top_courses=top_courses,
    )
