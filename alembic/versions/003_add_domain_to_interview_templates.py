"""add domain to interview_templates."""

import sqlalchemy as sa

from alembic import op

revision = "003_add_template_domain"

down_revision = "002_add_llm_usage"

branch_labels = None

depends_on = None


def upgrade() -> None:
    """Add domain column to interview_templates."""

    op.add_column(
        "interview_templates",
        sa.Column(
            "domain",
            sa.String(length=100),
            nullable=False,
            server_default="general",
        ),
    )

    op.create_index(
        "ix_interview_templates_domain",
        "interview_templates",
        ["domain"],
        unique=False,
    )


def downgrade() -> None:
    """Remove domain column."""

    op.drop_index(
        "ix_interview_templates_domain",
        table_name="interview_templates",
    )

    op.drop_column(
        "interview_templates",
        "domain",
    )
