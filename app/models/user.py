"""
User model for authentication and authorization.
"""

from flask_login import UserMixin
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models.base import TimestampMixin


class User(db.Model, UserMixin, TimestampMixin):  # type: ignore[name-defined]
    """
    User model for authentication.
    
    Attributes:
        id: Unique identifier
        username: Unique username
        email: Unique email address
        password_hash: Hashed password
        role: User role (admin, lecturer, viewer)
        is_active: Whether the account is active
        university_id: Optional link to a university (for scoping data)
    """

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="lecturer", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Optional: Link user to a university to scope their data
    university_id = Column(Integer, ForeignKey("university.id"), nullable=True)
    
    # Relationships
    university = relationship("University", backref="users")

    def set_password(self, password: str) -> None:
        """Set the password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check the password against the hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
