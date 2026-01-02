"""
Integration tests for university routes.

This module tests the Flask web interface for university management.
"""

from cli.university_cli import add_university


class TestUniversityIndexRoute:
    """Test university list route."""

    def test_index_empty(self, app, client):
        """Test listing universities when none exist."""
        with app.app_context():
            response = client.get("/universities/")
            assert response.status_code == 200
            assert b"Keine Hochschulen gefunden" in response.data

    def test_index_with_universities(self, app, client):
        """Test listing universities with data."""
        with app.app_context():
            add_university("TH Köln")
            add_university("RWTH Aachen")

            response = client.get("/universities/")
            assert response.status_code == 200
            assert b"TH K" in response.data  # Partial match for encoded umlaut
            assert b"RWTH Aachen" in response.data
            assert b"Hochschule(n) gefunden" in response.data
            assert b"<strong>2</strong>" in response.data

    def test_index_with_search(self, app, client):
        """Test searching universities."""
        with app.app_context():
            add_university("TH Köln")
            add_university("RWTH Aachen")
            add_university("Uni Köln")

            # Search by name
            response = client.get("/universities/?search=Köln")
            assert response.status_code == 200
            assert b"TH K" in response.data  # Partial match
            assert b"Uni K" in response.data  # Partial match
            assert b"RWTH Aachen" not in response.data

    def test_index_search_by_slug(self, app, client):
        """Test searching universities by slug."""
        with app.app_context():
            add_university("TH Köln", "th-koeln")
            add_university("RWTH Aachen", "rwth-aachen")

            response = client.get("/universities/?search=rwth")
            assert response.status_code == 200
            assert b"RWTH Aachen" in response.data
            assert b"TH K" not in response.data


class TestUniversityShowRoute:
    """Test university detail route."""

    def test_show_existing_university(self, app, client):
        """Test showing details of existing university."""
        with app.app_context():
            university = add_university("TH Köln")

            response = client.get(f"/universities/{university.id}")
            assert response.status_code == 200
            assert b"TH K" in response.data
            assert b"th-koeln" in response.data

    def test_show_nonexistent_university(self, app, client):
        """Test showing details of non-existent university."""
        with app.app_context():
            response = client.get("/universities/999")
            assert response.status_code == 302  # Redirect
            assert b"/universities/" in response.data  # Redirects to list


class TestUniversityNewRoute:
    """Test university creation route."""

    def test_new_get(self, app, client):
        """Test GET request to new university form."""
        with app.app_context():
            response = client.get("/universities/new")
            assert response.status_code == 200
            assert b"Neue Hochschule" in response.data
            assert b"Name" in response.data
            assert b"Slug" in response.data

    def test_new_post_success(self, app, client):
        """Test POST request to create new university."""
        with app.app_context():
            response = client.post(
                "/universities/new",
                data={"name": "TH Köln", "slug": "th-koeln"},
                follow_redirects=False,
            )

            assert response.status_code == 302  # Redirect
            assert b"/universities/" in response.data

            # Verify university was created
            from app.models.university import University
            from app import db

            university = db.session.query(University).filter_by(name="TH Köln").first()
            assert university is not None
            assert university.slug == "th-koeln"

    def test_new_post_auto_slug(self, app, client):
        """Test POST request with auto-generated slug."""
        with app.app_context():
            response = client.post(
                "/universities/new",
                data={"name": "TH Köln", "slug": ""},
                follow_redirects=False,
            )

            assert response.status_code == 302

            # Verify slug was auto-generated
            from app.models.university import University
            from app import db

            university = db.session.query(University).filter_by(name="TH Köln").first()
            assert university is not None
            assert university.slug == "th-koeln"

    def test_new_post_empty_name(self, app, client):
        """Test POST request with empty name."""
        with app.app_context():
            response = client.post(
                "/universities/new", data={"name": "", "slug": "test"}
            )

            assert response.status_code == 200  # Stays on form
            assert b"University name is required" in response.data

    def test_new_post_invalid_slug(self, app, client):
        """Test POST request with invalid slug."""
        with app.app_context():
            response = client.post(
                "/universities/new", data={"name": "TH Köln", "slug": "TH Köln"}
            )

            assert response.status_code == 200
            assert b"Invalid slug format" in response.data

    def test_new_post_duplicate_name(self, app, client):
        """Test POST request with duplicate name."""
        with app.app_context():
            add_university("TH Köln")

            response = client.post(
                "/universities/new", data={"name": "TH Köln", "slug": "test"}
            )

            assert response.status_code == 200
            assert b"already exists" in response.data


class TestUniversityEditRoute:
    """Test university edit route."""

    def test_edit_get(self, app, client):
        """Test GET request to edit university form."""
        with app.app_context():
            university = add_university("TH Köln")

            response = client.get(f"/universities/{university.id}/edit")
            assert response.status_code == 200
            assert b"Hochschule bearbeiten" in response.data
            assert b"TH K" in response.data

    def test_edit_get_nonexistent(self, app, client):
        """Test GET request to edit non-existent university."""
        with app.app_context():
            response = client.get("/universities/999/edit")
            assert response.status_code == 302  # Redirect

    def test_edit_post_success(self, app, client):
        """Test POST request to update university."""
        with app.app_context():
            university = add_university("TH Köln", "th-koeln")

            response = client.post(
                f"/universities/{university.id}/edit",
                data={"name": "Technische Hochschule Köln", "slug": "thk"},
                follow_redirects=False,
            )

            assert response.status_code == 302

            # Verify update
            from app.models.university import University
            from app import db

            updated = db.session.query(University).filter_by(id=university.id).first()
            assert updated.name == "Technische Hochschule Köln"
            assert updated.slug == "thk"

    def test_edit_post_empty_name(self, app, client):
        """Test POST request with empty name."""
        with app.app_context():
            university = add_university("TH Köln")

            response = client.post(
                f"/universities/{university.id}/edit",
                data={"name": "", "slug": "th-koeln"},
            )

            assert response.status_code == 200
            assert b"University name is required" in response.data

    def test_edit_post_invalid_slug(self, app, client):
        """Test POST request with invalid slug."""
        with app.app_context():
            university = add_university("TH Köln")

            response = client.post(
                f"/universities/{university.id}/edit",
                data={"name": "TH Köln", "slug": "TH_Köln"},
            )

            assert response.status_code == 200
            assert b"Invalid slug format" in response.data


class TestUniversityDeleteRoute:
    """Test university delete route."""

    def test_delete_get(self, app, client):
        """Test GET request to delete confirmation page."""
        with app.app_context():
            university = add_university("TH Köln")

            response = client.get(f"/universities/{university.id}/delete")
            assert response.status_code == 200
            assert b"Hochschule l" in response.data  # "löschen" with encoding
            assert b"TH K" in response.data

    def test_delete_get_nonexistent(self, app, client):
        """Test GET request to delete non-existent university."""
        with app.app_context():
            response = client.get("/universities/999/delete")
            assert response.status_code == 302

    def test_delete_post_success(self, app, client):
        """Test POST request to delete university."""
        with app.app_context():
            university = add_university("TH Köln")
            university_id = university.id

            response = client.post(
                f"/universities/{university_id}/delete", follow_redirects=False
            )

            assert response.status_code == 302
            assert b"/universities/" in response.data

            # Verify deletion
            from app.models.university import University
            from app import db

            deleted = db.session.query(University).filter_by(id=university_id).first()
            assert deleted is None

    def test_delete_post_nonexistent(self, app, client):
        """Test POST request to delete non-existent university."""
        with app.app_context():
            response = client.post("/universities/999/delete", follow_redirects=False)
            assert response.status_code == 302
