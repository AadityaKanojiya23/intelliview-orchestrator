"""merge template domain and candidate demographics migrations

Revision ID: b39909f765ee
Revises: 003_add_template_domain, ba062b2def4d
Create Date: 2026-08-17 05:09:30.784161

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b39909f765ee"
down_revision: Union[str, Sequence[str], None] = (
    "003_add_template_domain",
    "ba062b2def4d",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
