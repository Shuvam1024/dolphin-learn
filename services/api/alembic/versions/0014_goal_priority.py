"""goals.priority enum for planner breadth/depth/review reserve

Revision ID: 0014_goal_priority
Revises: 0013_sessions_target_minutes
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014_goal_priority"
down_revision: Union[str, Sequence[str], None] = "0013_sessions_target_minutes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "goals",
        sa.Column(
            "priority",
            sa.String(32),
            nullable=False,
            server_default="understand",
        ),
    )
    op.create_check_constraint(
        "ck_goals_priority",
        "goals",
        "priority IN ('understand', 'apply', 'make_it_stick')",
    )
    # Best-effort map from free-text objectives; default stays understand.
    op.execute(
        """
        UPDATE goals
        SET priority = CASE
            WHEN lower(coalesce(normalized_objective, '')) LIKE '%make it stick%'
              OR lower(coalesce(normalized_objective, '')) LIKE '%make_it_stick%'
              OR lower(coalesce(normalized_objective, '')) LIKE '%retention%'
              OR lower(coalesce(normalized_objective, '')) LIKE '%remember%'
            THEN 'make_it_stick'
            WHEN lower(coalesce(normalized_objective, '')) LIKE '%apply%'
              OR lower(coalesce(normalized_objective, '')) LIKE '%practice%'
              OR lower(coalesce(normalized_objective, '')) LIKE '%use it%'
            THEN 'apply'
            ELSE 'understand'
        END
        """
    )


def downgrade() -> None:
    op.drop_constraint("ck_goals_priority", "goals", type_="check")
    op.drop_column("goals", "priority")
