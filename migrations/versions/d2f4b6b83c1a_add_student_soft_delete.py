"""Add soft delete to student

Revision ID: d2f4b6b83c1a
Revises: 2917cc901cab
Create Date: 2026-01-11 23:04:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d2f4b6b83c1a"
down_revision: str | Sequence[str] | None = "2917cc901cab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("student", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_index(
        op.f("ix_student_deleted_at"), "student", ["deleted_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_student_deleted_at"), table_name="student")
    op.drop_column("student", "deleted_at")
