"""
Audit Service for logging user actions.

This module provides a service for creating audit logs.
"""

import json
from typing import Any, Optional

from flask import has_request_context, request
from flask_login import current_user

from app import db
from app.models.audit_log import AuditLog


class AuditService:
    """Service for managing audit logs."""

    @staticmethod
    def log(
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> AuditLog:
        """
        Create a new audit log entry.

        Args:
            action: The action performed (e.g., 'create', 'update', 'delete')
            target_type: The type of entity affected (e.g., 'Student', 'Course')
            target_id: The ID of the entity affected
            details: Additional details about the action
            user_id: ID of the user performing the action. If None, tries to get from current_user.

        Returns:
            The created AuditLog entry
        """
        # Determine user_id if not provided
        if user_id is None:
            if current_user and current_user.is_authenticated:
                user_id = current_user.id

        # Determine IP address if in request context
        ip_address = None
        if has_request_context():
            ip_address = request.remote_addr

        # Create log entry
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address,
        )

        db.session.add(audit_log)
        db.session.commit()

        return audit_log

    @staticmethod
    def get_logs_for_entity(target_type: str, target_id: int) -> list[AuditLog]:
        """
        Get all audit logs for a specific entity.

        Args:
            target_type: The type of entity
            target_id: The ID of the entity

        Returns:
            List of AuditLog entries
        """
        return (
            AuditLog.query.filter_by(target_type=target_type, target_id=target_id)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    @staticmethod
    def get_logs_by_user(user_id: int) -> list[AuditLog]:
        """
        Get all audit logs for a specific user.

        Args:
            user_id: The ID of the user

        Returns:
            List of AuditLog entries
        """
        return (
            AuditLog.query.filter_by(user_id=user_id)
            .order_by(AuditLog.created_at.desc())
            .all()
        )
