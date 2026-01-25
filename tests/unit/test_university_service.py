
import pytest
from app.services.university_service import UniversityService
from app.models.university import University

@pytest.fixture
def university_service():
    return UniversityService()

@pytest.fixture
def sample_university(db):
    uni = University(name="Initial Uni", slug="initial-uni")
    db.session.add(uni)
    db.session.commit()
    return uni

def test_generate_slug():
    assert UniversityService.generate_slug("TH Köln") == "th-koeln"
    assert UniversityService.generate_slug("Uni München") == "uni-muenchen"
    assert UniversityService.generate_slug("Test! @# Uni") == "test-uni"

def test_add_university_success(university_service, db):
    uni = university_service.add_university("New University")
    assert uni.id is not None
    assert uni.name == "New University"
    assert uni.slug == "new-university"

def test_add_university_custom_slug(university_service, db):
    uni = university_service.add_university("Custom Uni", slug="custom-slug")
    assert uni.slug == "custom-slug"

def test_add_university_validation_error(university_service, db):
    # Empty name
    with pytest.raises(ValueError, match="University name cannot be empty"):
        university_service.add_university("")
    
    # Invalid slug
    with pytest.raises(ValueError, match="Invalid slug format"):
        university_service.add_university("Test", slug="Invalid Slug!")

def test_list_universities(university_service, sample_university, db):
    university_service.add_university("Another Uni")
    
    # Search
    results = university_service.list_universities(search="Another")
    assert len(results) == 1
    assert results[0].name == "Another Uni"
    
    # All
    all_unis = university_service.list_universities()
    assert len(all_unis) == 2

def test_update_university(university_service, sample_university, db):
    updated = university_service.update_university(
        sample_university.id,
        name="Updated Name",
        slug="updated-slug"
    )
    assert updated.name == "Updated Name"
    assert updated.slug == "updated-slug"

def test_delete_university(university_service, sample_university, db):
    uni_id = sample_university.id
    result = university_service.delete_university(uni_id)
    assert result is True
    assert db.session.get(University, uni_id) is None
