"""ai_calls audit table and learner AI opt-out

Revision ID: 0011_ai_calls
Revises: 0010_activity_content_fields
Create Date: 2026-09-23

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0011_ai_calls"
down_revision: str | None = "0010_activity_content_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "learner_profiles",
        sa.Column("ai_opt_out", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_table(
        "ai_calls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("prompt_id", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "outcome IN ('ok', 'schema_error', 'unavailable', 'capped', 'disabled')",
            name="ck_ai_calls_outcome",
        ),
    )
    op.create_index("ix_ai_calls_user_id", "ai_calls", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_calls_user_id", table_name="ai_calls")
    op.drop_table("ai_calls")
    op.drop_column("learner_profiles", "ai_opt_out")
