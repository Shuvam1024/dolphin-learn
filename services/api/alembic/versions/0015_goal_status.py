"""goals.status check for active/paused/archived

Revision ID: 0015_goal_status
Revises: 0014_goal_priority
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015_goal_status"
down_revision: Union[str, Sequence[str], None] = "0014_goal_priority"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE goals SET status = 'active' "
        "WHERE status IS NULL OR status NOT IN ('active', 'paused', 'archived')"
    )
    op.create_check_constraint(
        "ck_goals_status",
        "goals",
        "status IN ('active', 'paused', 'archived')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_goals_status", "goals", type_="check")
