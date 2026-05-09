
import pytest
from app.services.course_service import CourseService
from app.models.course import Course
from app.models.university import University

@pytest.fixture
def course_service():
    return CourseService()

@pytest.fixture
def sample_course_data(db):
    university = University(name="Test Uni", slug="test-uni")
    db.session.add(university)
    db.session.commit()
    
    course = Course(
        name="Test Course",
        semester="2023_SoSe",
        slug="test-course",
        university_id=university.id
    )
    db.session.add(course)
    db.session.commit()
    return {
        "university": university,
        "course": course
    }

def test_add_course_success(course_service, sample_course_data, db):
    course = course_service.add_course(
        name="New Course",
        semester="2024_WiSe",
        university_id=sample_course_data["university"].id
    )
    assert course.id is not None
    assert course.name == "New Course"
    assert course.semester == "2024_WiSe"
    assert course.slug == "new-course"

def test_add_course_invalid_semester(course_service, sample_course_data, db):
    with pytest.raises(ValueError, match="Invalid semester format"):
        course_service.add_course(
            name="Bad Semester",
            semester="WS23", # Invalid format
            university_id=sample_course_data["university"].id
        )

def test_add_course_university_not_found(course_service, db):
    with pytest.raises(ValueError, match="University with ID 999 not found"):
        course_service.add_course(
            name="No Uni",
            semester="2023_SoSe",
            university_id=999
        )

def test_list_courses_filters(course_service, sample_course_data, db):
    # Add another course in different semester
    course_service.add_course(
        name="Winter Course",
        semester="2023_WiSe",
        university_id=sample_course_data["university"].id
    )
    
    # Filter by semester
    courses = course_service.list_courses(semester="2023_SoSe")
    assert len(courses) == 1
    assert courses[0].name == "Test Course"
    
    # Filter by university
    courses = course_service.list_courses(university_id=sample_course_data["university"].id)
    assert len(courses) == 2

def test_update_course(course_service, sample_course_data, db):
    updated = course_service.update_course(
        sample_course_data["course"].id,
        name="Updated Name",
        semester="2024_SoSe"
    )
    assert updated.name == "Updated Name"
    assert updated.semester == "2024_SoSe"
    assert updated.slug == "updated-name"

def test_delete_course(course_service, sample_course_data, db):
    course_id = sample_course_data["course"].id
    result = course_service.delete_course(course_id)
    assert result is True
    assert db.session.get(Course, course_id) is None

def test_delete_course_not_found(course_service, db):
    with pytest.raises(ValueError, match="Course with ID 999 not found"):
        course_service.delete_course(999)
