"""
Audit Log model definition.

This module defines the AuditLog model for tracking user actions within the system.
"""

from typing import Optional

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app import db
from app.models.base import TimestampMixin


class AuditLog(db.Model, TimestampMixin):  # type: ignore
    """
    Model for storing audit logs of system actions.

    Attributes:
        id: Primary key
        user_id: ID of the user who performed the action
        action: The type of action (e.g., 'create', 'update', 'delete', 'login')
        target_type: The type of entity affected (e.g., 'Student', 'Course')
        target_id: The ID of the entity affected
        details: JSON field storing additional details (e.g., changed fields)
        ip_address: IP address of the user (optional)
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    action = Column(String(50), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Relationships
    user = relationship("User", backref="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.target_type}:{self.target_id} by User:{self.user_id}>"
