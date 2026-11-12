"""
Unit tests for AuditService auto-commit removal.

Verifies that AuditService.log() no longer commits its own transaction,
allowing the caller to control commit/rollback.
"""

from app import db
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService


class TestAuditServiceNoAutoCommit:
    """Test that AuditService does not auto-commit."""

    def test_audit_entry_in_session_not_committed(self, app):
        """
        AuditService.log() should add the log to the session
        (db.session.new) but NOT commit. Verify via session.new.
        """
        # Log an audit entry
        AuditService.log(
            action="test_pending",
            target_type="TestModel",
            details={"key": "value"},
        )

        # The log should be in db.session.new (pending, not committed)
        pending_audit = [
            obj
            for obj in db.session.new
            if isinstance(obj, AuditLog) and obj.action == "test_pending"
        ]
        assert len(pending_audit) == 1, (
            "Audit log should be added to session but NOT committed"
        )

    def test_audit_log_rolled_back(self, app):
        """
        When the caller rolls back, the audit log should also be rolled back.
        This proves the audit log is in the caller's transaction.
        """
        # Log an audit entry
        AuditService.log(
            action="test_rollback",
            target_type="TestModel",
        )

        # Verify it's in session.new
        assert any(
            isinstance(obj, AuditLog) and obj.action == "test_rollback"
            for obj in db.session.new
        ), "Audit log should be in session"

        # Rollback
        db.session.rollback()

        # After rollback, it should NOT be in session.new or pending changes
        assert not any(
            isinstance(obj, AuditLog) and obj.action == "test_rollback"
            for obj in db.session.new
        ), "Audit log should be rolled back - AuditService.log() must not auto-commit"

        # Also not in pending changes
        assert not any(
            isinstance(obj, AuditLog) and obj.action == "test_rollback"
            for obj in db.session.dirty
        ), "Audit log should not be in pending changes after rollback"
