
import pytest
from datetime import date
from app.services.exam_service import ExamService
from app.models.exam import Exam
from app.models.course import Course
from app.models.university import University

@pytest.fixture
def exam_service():
    return ExamService()

@pytest.fixture
def exam_test_data(db):
    uni = University(name="Exam Uni", slug="exam-uni")
    db.session.add(uni)
    db.session.commit()
    
    course = Course(name="Exam Course", semester="2023_SoSe", slug="exam-course", university_id=uni.id)
    db.session.add(course)
    db.session.commit()
    
    return {
        "university": uni,
        "course": course
    }

def test_add_exam_success(exam_service, exam_test_data, db):
    exam = exam_service.add_exam(
        name="Final Exam",
        course_id=exam_test_data["course"].id,
        exam_date=date(2023, 7, 15),
        max_points=100.0,
        weight=100.0,
        description="The big one"
    )
    assert exam.id is not None
    assert exam.name == "Final Exam"
    assert exam.max_points == 100.0

def test_add_exam_validation_error(exam_service, exam_test_data, db):
    # Empty name
    with pytest.raises(ValueError, match="Exam name cannot be empty"):
        exam_service.add_exam("", exam_test_data["course"].id, date.today(), 100.0)
    
    # Invalid max points
    with pytest.raises(ValueError, match="Maximum points must be greater than 0"):
        exam_service.add_exam("Test", exam_test_data["course"].id, date.today(), 0)
        
    # Invalid weight
    with pytest.raises(ValueError, match="Weight must be between 0 and 100"):
        exam_service.add_exam("Test", exam_test_data["course"].id, date.today(), 100.0, weight=101.0)

def test_list_exams(exam_service, exam_test_data, db):
    exam_service.add_exam("Exam 1", exam_test_data["course"].id, date(2023, 1, 1), 100.0)
    exam_service.add_exam("Exam 2", exam_test_data["course"].id, date(2023, 2, 1), 100.0)
    
    results = exam_service.list_exams(course_id=exam_test_data["course"].id)
    assert len(results) == 2
    assert results[0].name == "Exam 2" # Descending date order

def test_update_exam(exam_service, exam_test_data, db):
    exam = exam_service.add_exam("Initial Name", exam_test_data["course"].id, date.today(), 100.0)
    
    updated = exam_service.update_exam(exam.id, name="Updated Name", max_points=120.0)
    assert updated.name == "Updated Name"
    assert updated.max_points == 120.0

def test_delete_exam(exam_service, exam_test_data, db):
    exam = exam_service.add_exam("Delete Me", exam_test_data["course"].id, date.today(), 100.0)
    exam_id = exam.id
    
    result = exam_service.delete_exam(exam_id)
    assert result is True
    assert db.session.get(Exam, exam_id) is None
