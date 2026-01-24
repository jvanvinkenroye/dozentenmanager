import pytest
from datetime import date
from app.models.university import University
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.grade import Grade
from app.services.grade_service import GradeService

@pytest.fixture
def grade_service(db):
    return GradeService()

@pytest.fixture
def setup_data(db):
    """Set up basic data for grade tests."""
    uni = University(name="Test Uni", slug="test-uni")
    db.session.add(uni)
    db.session.flush()

    student = Student(
        first_name="John", 
        last_name="Doe", 
        email="john@example.com", 
        student_id="12345678",
        program="Computer Science"
    )
    db.session.add(student)
    
    course = Course(
        name="Math 101", 
        slug="math-101", 
        semester="WS23/24", 
        university_id=uni.id
    )
    db.session.add(course)
    db.session.flush()

    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        status="active"
    )
    db.session.add(enrollment)
    
    exam = Exam(
        name="Final Exam",
        course_id=course.id,
        exam_date=date.today(),
        max_points=100.0,
        weight=100.0
    )
    db.session.add(exam)
    db.session.commit()

    return {
        "uni": uni,
        "student": student,
        "course": course,
        "enrollment": enrollment,
        "exam": exam
    }

def test_add_grade_success(grade_service, setup_data):
    """Test adding a valid grade."""
    data = setup_data
    grade = grade_service.add_grade(
        enrollment_id=data["enrollment"].id,
        exam_id=data["exam"].id,
        points=95.0,
        is_final=True
    )
    
    assert grade.points == 95.0
    assert grade.percentage == 95.0
    assert grade.grade_value == 1.0  # 95% is 1.0
    assert grade.is_final is True
    assert grade.enrollment_id == data["enrollment"].id

def test_add_grade_validation(grade_service, setup_data):
    """Test validation when adding a grade."""
    data = setup_data
    
    # Points < 0
    with pytest.raises(ValueError, match="Points must be between"):
        grade_service.add_grade(
            enrollment_id=data["enrollment"].id,
            exam_id=data["exam"].id,
            points=-5.0
        )
        
    # Points > max
    with pytest.raises(ValueError, match="Points must be between"):
        grade_service.add_grade(
            enrollment_id=data["enrollment"].id,
            exam_id=data["exam"].id,
            points=105.0
        )

def test_add_grade_duplicate(grade_service, setup_data):
    """Test preventing duplicate grades."""
    data = setup_data
    
    grade_service.add_grade(
        enrollment_id=data["enrollment"].id,
        exam_id=data["exam"].id,
        points=80.0
    )
    
    with pytest.raises(ValueError, match="Grade already exists"):
        grade_service.add_grade(
            enrollment_id=data["enrollment"].id,
            exam_id=data["exam"].id,
            points=85.0
        )

def test_add_exam_component_and_grade(grade_service, setup_data):
    """Test adding an exam component and grading it."""
    data = setup_data
    
    # Add component
    component = grade_service.add_exam_component(
        exam_id=data["exam"].id,
        name="Part 1",
        weight=50.0,
        max_points=50.0
    )
    
    # Grade component
    grade = grade_service.add_grade(
        enrollment_id=data["enrollment"].id,
        exam_id=data["exam"].id,
        component_id=component.id,
        points=40.0
    )
    
    assert grade.component_id == component.id
    assert grade.points == 40.0
    assert grade.percentage == 80.0  # 40/50
    assert grade.grade_value == 2.0  # 80% is 2.0

def test_update_grade(grade_service, setup_data):
    """Test updating a grade."""
    data = setup_data
    
    grade = grade_service.add_grade(
        enrollment_id=data["enrollment"].id,
        exam_id=data["exam"].id,
        points=50.0
    )
    
    assert grade.grade_value == 4.0 # 50%
    
    updated = grade_service.update_grade(
        grade_id=grade.id,
        points=90.0
    )
    
    assert updated.points == 90.0
    assert updated.percentage == 90.0
    assert updated.grade_value == 1.3
    assert updated.grade_label == "sehr gut"

def test_delete_grade(grade_service, setup_data):
    """Test deleting a grade."""
    data = setup_data
    
    grade = grade_service.add_grade(
        enrollment_id=data["enrollment"].id,
        exam_id=data["exam"].id,
        points=75.0
    )
    
    grade_id = grade.id
    assert grade_service.delete_grade(grade_id)
    
    with pytest.raises(ValueError, match="not found"):
        grade_service.get_grade(grade_id)

def test_list_grades(grade_service, setup_data):
    """Test listing grades with filters."""
    data = setup_data
    
    grade1 = grade_service.add_grade(
        enrollment_id=data["enrollment"].id,
        exam_id=data["exam"].id,
        points=90.0,
        is_final=True
    )
    
    grades = grade_service.list_grades(enrollment_id=data["enrollment"].id)
    assert len(grades) == 1
    assert grades[0].id == grade1.id
    
    grades = grade_service.list_grades(is_final=False)
    assert len(grades) == 0

def test_calculate_weighted_average(grade_service, db):
    """Test weighted average calculation."""
    # Setup uni, course, student, enrollment
    uni = University(name="Uni2", slug="uni2")
    db.session.add(uni)
    db.session.flush()
    
    course = Course(name="Physics", slug="phys", semester="SS24", university_id=uni.id)
    db.session.add(course)
    db.session.flush()
    
    student = Student(first_name="Jane", last_name="Doe", email="jane@ex.com", student_id="99999999", program="Physics")
    db.session.add(student)
    db.session.flush()
    
    enrollment = Enrollment(student_id=student.id, course_id=course.id, status="active")
    db.session.add(enrollment)
    db.session.flush()
    
    # Exam 1 (60% weight)
    exam1 = Exam(name="Midterm", course_id=course.id, exam_date=date.today(), max_points=100.0, weight=60.0)
    db.session.add(exam1)
    
    # Exam 2 (40% weight)
    exam2 = Exam(name="Final", course_id=course.id, exam_date=date.today(), max_points=100.0, weight=40.0)
    db.session.add(exam2)
    db.session.commit()
    
    # Grade for Exam 1: 90 points (1.3)
    grade_service.add_grade(
        enrollment_id=enrollment.id,
        exam_id=exam1.id,
        points=90.0,
        is_final=True
    )
    
    # Grade for Exam 2: 50 points (4.0)
    grade_service.add_grade(
        enrollment_id=enrollment.id,
        exam_id=exam2.id,
        points=50.0,
        is_final=True
    )
    
    # Weighted Average Calculation
    # Exam 1: 1.3 * 0.6 = 0.78
    # Exam 2: 4.0 * 0.4 = 1.6
    # Total: 2.38
    
    result = grade_service.calculate_weighted_average(enrollment.id)
    assert result is not None
    assert 2.3 <= result["weighted_average"] <= 2.4
    assert result["is_passing"] is True

def test_get_exam_statistics(grade_service, setup_data, db):
    """Test exam statistics calculation."""
    data = setup_data
    exam = data["exam"]
    
    # Create another student
    student2 = Student(first_name="Bob", last_name="Smith", email="bob@ex.com", student_id="88888888", program="Computer Science")
    db.session.add(student2)
    db.session.flush()
    
    enrollment2 = Enrollment(student_id=student2.id, course_id=data["course"].id, status="active")
    db.session.add(enrollment2)
    db.session.commit()
    
    # Grade 1: 100 points
    grade_service.add_grade(
        enrollment_id=data["enrollment"].id,
        exam_id=exam.id,
        points=100.0
    )
    
    # Grade 2: 50 points
    grade_service.add_grade(
        enrollment_id=enrollment2.id,
        exam_id=exam.id,
        points=50.0
    )
    
    stats = grade_service.get_exam_statistics(exam.id)
    
    assert stats["total_students"] == 2
    assert stats["points"]["max"] == 100.0
    assert stats["points"]["min"] == 50.0
    assert stats["points"]["avg"] == 75.0
    assert stats["pass_rate"] == 100.0

def test_add_exam_component_validation(grade_service, setup_data):
    """Test validation when adding exam components."""
    data = setup_data
    
    # Add component with 60% weight
    grade_service.add_exam_component(
        exam_id=data["exam"].id,
        name="Comp 1",
        weight=60.0,
        max_points=100.0
    )
    
    # Try adding another with 50% (Total 110%) -> Should fail
    with pytest.raises(ValueError, match="Total component weight"):
        grade_service.add_exam_component(
            exam_id=data["exam"].id,
            name="Comp 2",
            weight=50.0,
            max_points=100.0
        )

def test_create_default_grading_scale(grade_service):
    """Test creating default grading scale."""
    scale = grade_service.create_default_grading_scale()
    
    assert scale.name == "Deutsche Notenskala"
    assert scale.is_default is True
    assert len(scale.thresholds) == 11 # 1.0 to 5.0 (including 1.3, 1.7 etc)