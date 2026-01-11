"""Merge heads

Revision ID: 3733045ba0f3
Revises: 9b633f2b48b1, d2f4b6b83c1a
Create Date: 2026-01-11 23:47:03.034027

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3733045ba0f3"
down_revision: str | Sequence[str] | None = ("9b633f2b48b1", "d2f4b6b83c1a")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
