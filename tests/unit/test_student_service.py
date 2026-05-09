import pytest
from app.services.student_service import StudentService
from app.models.student import Student

@pytest.fixture
def student_service():
    return StudentService()

@pytest.fixture
def sample_student(db):
    student = Student(
        first_name="Max",
        last_name="Mustermann",
        student_id="12345678",
        email="max.mustermann@example.com",
        program="Computer Science"
    )
    db.session.add(student)
    db.session.commit()
    return student

def test_add_student_success(student_service, db):
    student = student_service.add_student(
        first_name="Erika",
        last_name="Musterfrau",
        student_id="87654321",
        email="erika.musterfrau@example.com",
        program="Physics"
    )
    assert student.id is not None
    assert student.first_name == "Erika"
    assert student.student_id == "87654321"

def test_add_student_validation_error(student_service, db):
    # Empty name
    with pytest.raises(ValueError, match="First name cannot be empty"):
        student_service.add_student(
            first_name="",
            last_name="Doe",
            student_id="12345678",
            email="doe@example.com",
            program="CS"
        )
    
    # Invalid ID
    with pytest.raises(ValueError, match="Ungültiges Matrikelnummer-Format"):
        student_service.add_student(
            first_name="John",
            last_name="Doe",
            student_id="123",
            email="doe@example.com",
            program="CS"
        )

def test_add_student_duplicate_error(student_service, sample_student):
    # Duplicate ID
    with pytest.raises(ValueError, match="Student mit Matrikelnummer '12345678' existiert bereits"):
        student_service.add_student(
            first_name="John",
            last_name="Doe",
            student_id="12345678",
            email="new@example.com",
            program="CS"
        )
        
    # Duplicate Email (use a unique student_id here to trigger email error)
    with pytest.raises(ValueError, match="Student mit E-Mail-Adresse 'max.mustermann@example.com' existiert bereits"):
        student_service.add_student(
            first_name="John",
            last_name="Doe",
            student_id="00000000",
            email="max.mustermann@example.com",
            program="CS"
        )

def test_get_student(student_service, sample_student):
    # By DB ID
    found = student_service.get_student(sample_student.id)
    assert found is not None
    assert found.id == sample_student.id
    
    # By Student ID
    found_by_id = student_service.get_student_by_student_id(sample_student.student_id)
    assert found_by_id is not None
    assert found_by_id.id == sample_student.id

def test_list_students_search(student_service, sample_student, db):
    # Add another student
    s2 = Student(
        first_name="John", last_name="Doe", student_id="11111111",
        email="john@doe.com", program="Mathematics"
    )
    db.session.add(s2)
    db.session.commit()
    
    # Search by name
    results = student_service.list_students(search="Muster")
    assert len(results) >= 1
    assert any(r.last_name == "Mustermann" for r in results)
    
    # Search by program
    results = student_service.list_students(program="Math")
    assert len(results) >= 1
    assert any(r.program == "Mathematics" for r in results)

def test_update_student(student_service, sample_student):
    updated = student_service.update_student(
        sample_student.id,
        first_name="Maximilian",
        program="Data Science"
    )
    assert updated.first_name == "Maximilian"
    assert updated.program == "Data Science"
    assert updated.last_name == "Mustermann" # Should remain unchanged

def test_delete_student(student_service, sample_student, db):
    result = student_service.delete_student(sample_student.id)
    assert result is True
    
    # Check soft delete
    deleted = db.session.get(Student, sample_student.id)
    assert deleted.deleted_at is not None
    
    # Should not be found by service getter
    assert student_service.get_student(sample_student.id) is None