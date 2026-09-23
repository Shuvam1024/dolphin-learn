"""goals.domain_key required against seeded domains

Revision ID: 0009_goal_domain_key
Revises: 0008_attempt_idempotency
Create Date: 2026-09-23

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0009_goal_domain_key"
down_revision: str | None = "0008_attempt_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("goals", sa.Column("domain_key", sa.String(length=64), nullable=True))
    op.execute(sa.text("UPDATE goals SET domain_key = 'python' WHERE domain_key IS NULL"))
    op.alter_column("goals", "domain_key", existing_type=sa.String(length=64), nullable=False)
    op.create_foreign_key(
        "fk_goals_domain_key",
        "goals",
        "domains",
        ["domain_key"],
        ["key"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_goals_domain_key", "goals", type_="foreignkey")
    op.drop_column("goals", "domain_key")
