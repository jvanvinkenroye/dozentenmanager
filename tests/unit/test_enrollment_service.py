
import pytest
from datetime import date
from app.services.enrollment_service import EnrollmentService
from app.models.student import Student
from app.models.course import Course
from app.models.university import University
from app.models.enrollment import Enrollment

@pytest.fixture
def enrollment_service():
    return EnrollmentService()

@pytest.fixture
def enrollment_test_data(db):
    uni = University(name="Enroll Uni", slug="enroll-uni")
    db.session.add(uni)
    db.session.commit()
    
    course = Course(name="Enroll Course", semester="2023_SoSe", slug="enroll-course", university_id=uni.id)
    db.session.add(course)
    db.session.commit()
    
    student = Student(
        first_name="Alice", last_name="Enroll", student_id="11223344", 
        email="alice@enroll.com", program="CS"
    )
    db.session.add(student)
    db.session.commit()
    
    return {
        "university": uni,
        "course": course,
        "student": student
    }

def test_add_enrollment_success(enrollment_service, enrollment_test_data, db):
    enr = enrollment_service.add_enrollment(
        student_id_str=enrollment_test_data["student"].student_id,
        course_id=enrollment_test_data["course"].id
    )
    assert enr.id is not None
    assert enr.student_id == enrollment_test_data["student"].id
    assert enr.course_id == enrollment_test_data["course"].id
    assert enr.status == "active"

def test_add_enrollment_student_not_found(enrollment_service, enrollment_test_data, db):
    with pytest.raises(ValueError, match="Student mit Matrikelnummer 99999999 nicht gefunden"):
        enrollment_service.add_enrollment("99999999", enrollment_test_data["course"].id)

def test_update_enrollment_status(enrollment_service, enrollment_test_data, db):
    # Add enrollment first
    student_id = enrollment_test_data["student"].student_id
    course_id = enrollment_test_data["course"].id
    enrollment_service.add_enrollment(student_id, course_id)
    
    # Update status to completed
    updated = enrollment_service.update_enrollment_status(student_id, course_id, "completed")
    assert updated.status == "completed"
    
    # Update status to dropped
    updated = enrollment_service.update_enrollment_status(student_id, course_id, "dropped")
    assert updated.status == "dropped"
    assert updated.unenrollment_date == date.today()

def test_remove_enrollment(enrollment_service, enrollment_test_data, db):
    student_id = enrollment_test_data["student"].student_id
    course_id = enrollment_test_data["course"].id
    enr = enrollment_service.add_enrollment(student_id, course_id)
    enr_id = enr.id
    
    result = enrollment_service.remove_enrollment(student_id, course_id)
    assert result is True
    
    # Verify deletion
    assert db.session.get(Enrollment, enr_id) is None
    assert enrollment_service.get_enrollment(student_id, course_id) is None

def test_list_enrollments(enrollment_service, enrollment_test_data, db):
    student_id = enrollment_test_data["student"].student_id
    course_id = enrollment_test_data["course"].id
    enrollment_service.add_enrollment(student_id, course_id)
    
    # List by course
    results = enrollment_service.list_enrollments(course_id=course_id)
    assert len(results) == 1
    assert results[0].student_id == enrollment_test_data["student"].id
    
    # List by student
    results = enrollment_service.list_enrollments(student_id_str=student_id)
    assert len(results) == 1
    assert results[0].course_id == course_id
