"""
Unit tests for password hashing security.

Verifies that the User model uses scrypt (not the weaker PBKDF2)
for password hashing, and that both setting and checking passwords
work correctly.
"""

from werkzeug.security import check_password_hash, generate_password_hash


class TestPasswordHashing:
    """Test password hashing security."""

    def test_set_password_uses_scrypt(self, app, db):
        """
        User.set_password() should use scrypt (not PBKDF2).
        scrypt hashes start with 'scrypt:'.
        """
        from app.models.user import User

        user = User(username="scrypt_test", email="scrypt@test.com", role="admin")
        user.set_password("testpassword")

        # scrypt hashes start with 'scrypt:'
        assert user.password_hash.startswith("scrypt:"), (
            f"Expected scrypt hash (starts with 'scrypt:'), got: {user.password_hash[:20]}"
        )

    def test_check_password_scrypt(self, app, db):
        """Password verification should work with scrypt hashes."""
        from app.models.user import User

        user = User(username="check_test", email="check@test.com", role="admin")
        user.set_password("correctpassword")

        assert user.check_password("correctpassword") is True
        assert user.check_password("wrongpassword") is False

    def test_scrypt_produces_unique_hashes(self, app, db):
        """Same password should produce different scrypt hashes (different salt)."""
        from app.models.user import User

        user1 = User(username="unique_test_1", email="u1@test.com", role="admin")
        user2 = User(username="unique_test_2", email="u2@test.com", role="admin")
        user1.set_password("samepassword")
        user2.set_password("samepassword")

        assert user1.password_hash != user2.password_hash, (
            "Different users should have different password hashes (different salt)"
        )

    def test_scrypt_vs_pbkdf2(self):
        """
        Verify scrypt is used instead of PBKDF2.
        This is a direct comparison of the hashing methods.
        """
        scrypt_hash = generate_password_hash("test", method="scrypt")
        pbkdf2_hash = generate_password_hash("test", method="pbkdf2:sha256")

        assert scrypt_hash.startswith("scrypt:")
        assert pbkdf2_hash.startswith("pbkdf2:")
        assert scrypt_hash != pbkdf2_hash

    def test_check_password_works_with_both_methods(self):
        """
        check_password_hash supports both scrypt and PBKDF2.
        Existing PBKDF2 hashes should still verify.
        """
        # Old-style PBKDF2 hash
        old_hash = generate_password_hash("test", method="pbkdf2:sha256")
        # New-style scrypt hash
        new_hash = generate_password_hash("test", method="scrypt")

        assert check_password_hash(old_hash, "test") is True
        assert check_password_hash(new_hash, "test") is True
        assert check_password_hash(old_hash, "wrong") is False
        assert check_password_hash(new_hash, "wrong") is False
