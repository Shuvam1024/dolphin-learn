"""adult acknowledgment timestamp on learner profiles

Revision ID: 0004_adult_acknowledgment
Revises: 0003_learner_profiles
Create Date: 2026-09-23

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0004_adult_acknowledgment"
down_revision: str | None = "0003_learner_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "learner_profiles",
        sa.Column("adult_acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("learner_profiles", "adult_acknowledged_at")
