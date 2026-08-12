"""add demographics to candidates

Revision ID: ba062b2def4d
Revises: 002_add_llm_usage
Create Date: 2026-08-12 21:57:23.248966
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ba062b2def4d"
down_revision: str | Sequence[str] | None = "002_add_llm_usage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "candidates",
        sa.Column("demographics", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("candidates", "demographics")
