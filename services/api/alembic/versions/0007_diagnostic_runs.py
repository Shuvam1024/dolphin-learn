"""diagnostic runs that cannot claim mastery

Revision ID: 0007_diagnostic_runs
Revises: 98b0fc485c6b
Create Date: 2026-09-23

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0007_diagnostic_runs"
down_revision: str | None = "98b0fc485c6b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diagnostic_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("answered_count", sa.Integer(), nullable=False),
        sa.Column("mastery_claimed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('skipped', 'recorded')", name="ck_diagnostic_runs_status"),
        sa.CheckConstraint("mastery_claimed = false", name="ck_diagnostic_runs_no_mastery"),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_diagnostic_runs_user_id", "diagnostic_runs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_diagnostic_runs_user_id", table_name="diagnostic_runs")
    op.drop_table("diagnostic_runs")
