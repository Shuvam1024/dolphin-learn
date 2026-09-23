"""idempotency key on attempts

Revision ID: 0008_attempt_idempotency
Revises: 0007_diagnostic_runs
Create Date: 2026-09-23

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0008_attempt_idempotency"
down_revision: str | None = "0007_diagnostic_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attempts", sa.Column("idempotency_key", sa.String(length=64), nullable=True))
    op.create_unique_constraint(
        "uq_attempts_idempotency",
        "attempts",
        ["session_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_attempts_idempotency", "attempts", type_="unique")
    op.drop_column("attempts", "idempotency_key")
