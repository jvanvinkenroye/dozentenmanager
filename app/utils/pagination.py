"""
Pagination utility for list views.

This module provides helper functions and classes for implementing
pagination in Flask routes with consistent behavior across the application.
"""

from typing import Any

from flask import request
from sqlalchemy.orm import Query


class Pagination:
    """
    Pagination helper class with navigation methods.

    Attributes:
        items: List of items for the current page
        page: Current page number (1-indexed)
        per_page: Number of items per page
        total: Total number of items across all pages
        pages: Total number of pages
        has_prev: Whether there is a previous page
        has_next: Whether there is a next page
        prev_num: Previous page number or None
        next_num: Next page number or None
    """

    def __init__(
        self,
        items: list[Any],
        page: int,
        per_page: int,
        total: int,
    ):
        """
        Initialize pagination.

        Args:
            items: List of items for the current page
            page: Current page number (1-indexed)
            per_page: Number of items per page
            total: Total number of items across all pages
        """
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None

    def iter_pages(
        self,
        left_edge: int = 2,
        left_current: int = 2,
        right_current: int = 2,
        right_edge: int = 2,
    ):
        """
        Iterate over page numbers with ellipsis for gaps.

        Args:
            left_edge: Number of pages at the start
            left_current: Number of pages before current
            right_current: Number of pages after current
            right_edge: Number of pages at the end

        Yields:
            Page numbers or None for gaps (rendered as ...)

        Example:
            [1, 2, None, 5, 6, 7, 8, 9, None, 19, 20]
            Renders as: 1 2 ... 5 6 7 8 9 ... 19 20
        """
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (
                    num > self.page - left_current - 1
                    and num < self.page + right_current
                )
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


def paginate_query(
    query: Query,
    page: int | None = None,
    per_page: int = 20,
    error_out: bool = False,
) -> Pagination:
    """
    Paginate a SQLAlchemy query.

    Args:
        query: SQLAlchemy query to paginate
        page: Page number (1-indexed), defaults to request.args.get('page', 1)
        per_page: Items per page (default: 20)
        error_out: Raise error if page is out of range (default: False)

    Returns:
        Pagination object with items and navigation info

    Raises:
        ValueError: If page < 1 or page > pages (when error_out=True)

    Example:
        pagination = paginate_query(Student.query.order_by(Student.last_name))
        students = pagination.items
    """
    # Get page from request if not provided
    if page is None:
        page = request.args.get("page", 1, type=int)

    # Validate page number
    if page < 1:
        if error_out:
            raise ValueError("Page number must be >= 1")
        page = 1

    # Get total count
    total = query.count()

    # Calculate pagination
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    # Validate page doesn't exceed total pages
    if page > pages > 0:
        if error_out:
            raise ValueError(f"Page {page} exceeds total pages {pages}")
        page = pages

    # Get items for current page
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()

    return Pagination(items=items, page=page, per_page=per_page, total=total)


def get_pagination_args() -> tuple[int, int]:
    """
    Get pagination arguments from request.

    Returns:
        Tuple of (page, per_page) from request args with sensible defaults

    Example:
        page, per_page = get_pagination_args()
        pagination = paginate_query(query, page, per_page)
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Ensure valid values
    page = max(1, page)
    per_page = min(max(1, per_page), 100)  # Cap at 100 items per page

    return page, per_page
