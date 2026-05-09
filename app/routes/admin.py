"""
Admin routes blueprint.

This module provides routes for administrative tasks such as viewing audit logs.
"""

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.models.audit_log import AuditLog
from app.utils.auth import admin_required
from app.utils.pagination import get_pagination_args

# Create blueprint
bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/audit-logs")
@login_required
@admin_required
def audit_logs():
    """
    List all audit logs with pagination.
    """
    page, per_page = get_pagination_args()
    
    # Base query
    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    
    # Filtering by action
    action = request.args.get("action")
    if action:
        query = query.filter_by(action=action)
        
    # Filtering by target type
    target_type = request.args.get("target_type")
    if target_type:
        query = query.filter_by(target_type=target_type)

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        "admin/audit_logs.html",
        pagination=pagination,
        audit_logs=pagination.items,
        current_action=action,
        current_target_type=target_type
    )
