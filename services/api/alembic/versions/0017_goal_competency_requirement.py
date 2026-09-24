"""goal_competencies.requirement for placement skips

Revision ID: 0017_goal_competency_requirement
Revises: 0016_owned_competencies
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017_goal_competency_requirement"
down_revision: Union[str, Sequence[str], None] = "0016_owned_competencies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "goal_competencies",
        sa.Column("requirement", sa.String(length=32), nullable=False, server_default="required"),
    )
    op.create_check_constraint(
        "ck_goal_competencies_requirement",
        "goal_competencies",
        "requirement IN ('required', 'skipped')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_goal_competencies_requirement", "goal_competencies", type_="check")
    op.drop_column("goal_competencies", "requirement")
