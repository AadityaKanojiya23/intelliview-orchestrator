"""merge template domain and candidate demographics migrations

Revision ID: b39909f765ee
Revises: 003_add_template_domain, ba062b2def4d
Create Date: 2026-08-17 05:09:30.784161

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "b39909f765ee"
down_revision: str | Sequence[str] | None = (
    "003_add_template_domain",
    "ba062b2def4d",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
