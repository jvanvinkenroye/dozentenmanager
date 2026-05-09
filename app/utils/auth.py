"""
Authentication and authorization utilities.
"""

from functools import wraps
from typing import Callable, Any

from flask import abort
from flask_login import current_user


def role_required(*roles: str) -> Callable:
    """
    Decorator to restrict access to users with specific roles.

    Args:
        *roles: List of allowed roles (e.g. "admin", "lecturer")

    Returns:
        Decorated function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f: Callable) -> Callable:
    """Decorator to restrict access to admins only."""
    return role_required("admin")(f)


def lecturer_required(f: Callable) -> Callable:
    """Decorator to restrict access to lecturers and admins."""
    return role_required("admin", "lecturer")(f)
