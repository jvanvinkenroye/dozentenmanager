"""Add composite performance indexes

Revision ID: a1b2c3d4e5f6
Revises: d4bfc60b785e
Create Date: 2026-07-02 12:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "d4bfc60b785e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add composite indexes to improve query performance."""
    # enrollment(course_id, status) – speeds up "active enrollments for course" queries
    op.create_index(
        "idx_enrollment_course_status",
        "enrollment",
        ["course_id", "status"],
    )

    # student(deleted_at, last_name, first_name) – speeds up sorted non-deleted student queries
    op.create_index(
        "idx_student_deleted_name",
        "student",
        ["deleted_at", "last_name", "first_name"],
    )

    # grade(is_final, exam_id) – speeds up dashboard queries filtering final grades per exam
    op.create_index(
        "idx_grade_final_exam",
        "grade",
        ["is_final", "exam_id"],
    )

    # submission(enrollment_id, status) – speeds up filtering submissions by enrollment + status
    op.create_index(
        "idx_submission_enrollment_status",
        "submission",
        ["enrollment_id", "status"],
    )


def downgrade() -> None:
    """Remove composite performance indexes."""
    op.drop_index("idx_submission_enrollment_status", table_name="submission")
    op.drop_index("idx_grade_final_exam", table_name="grade")
    op.drop_index("idx_student_deleted_name", table_name="student")
    op.drop_index("idx_enrollment_course_status", table_name="enrollment")
