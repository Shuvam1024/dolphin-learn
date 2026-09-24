"""sessions.target_minutes for sitting size

Revision ID: 0013_sessions_target_minutes
Revises: 0012_evaluation_feedback_json
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_sessions_target_minutes"
down_revision: Union[str, Sequence[str], None] = "0012_evaluation_feedback_json"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("target_minutes", sa.Integer(), nullable=False, server_default="25"),
    )
    op.create_check_constraint(
        "ck_sessions_target_minutes",
        "sessions",
        "target_minutes >= 5 AND target_minutes <= 180",
    )


def downgrade() -> None:
    op.drop_constraint("ck_sessions_target_minutes", "sessions", type_="check")
    op.drop_column("sessions", "target_minutes")
