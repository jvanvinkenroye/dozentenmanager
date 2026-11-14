"""
Safe redirect utility to prevent open redirect attacks.

This module provides a safe_redirect function that validates redirect URLs
against open redirect vulnerabilities. Only same-origin and relative URLs
are allowed; external URLs are blocked and fall back to the default.

Usage:
    from app.utils.redirect import safe_redirect

    @app.route("/redirect")
    def redirect_view():
        url = request.args.get("next", "/")
        return redirect(safe_redirect(url, url_for("index")))
"""

from urllib.parse import urlsplit


def is_same_origin(url: str | None) -> bool:
    """
    Check if a URL is same-origin (safe to redirect to).

    Relative URLs (no scheme/host) are always considered same-origin.
    URLs with different hosts, protocol-relative URLs, javascript: and
    data: URLs are considered unsafe.

    Args:
        url: The URL to check, or None.

    Returns:
        True if the URL is safe to redirect to, False otherwise.
    """
    if url is None:
        return True

    if url.startswith("//") or url.startswith("javascript:") or url.startswith("data:"):
        return False

    parts = urlsplit(url)

    # Only scheme and netloc should be empty for relative URLs
    if parts.scheme or parts.netloc:
        # Has a scheme or host — check if same origin
        return parts.scheme == "" and parts.netloc == ""

    return True


def safe_redirect(
    url: str | None, default_url: str = "/", fallback_safe: bool = True
) -> str:
    """
    Safely redirect to a URL, falling back to default_url if unsafe.

    This function prevents open redirect attacks by only allowing same-origin
    URLs. External URLs are blocked and the default_url is returned instead.

    Args:
        url: The requested redirect URL.
        default_url: The fallback URL if the requested URL is unsafe or None.
        fallback_safe: If True, return default_url for unsafe URLs.
                       If False, return an empty string.

    Returns:
        The safe redirect URL (either the input or default).
    """
    if url and is_same_origin(url):
        return url

    if fallback_safe:
        return default_url

    return ""
