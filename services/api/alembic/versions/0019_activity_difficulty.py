"""activity_versions.difficulty for adaptive item selection

Revision ID: 0019_activity_difficulty
Revises: 0018_learner_effort_factors
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019_activity_difficulty"
down_revision: Union[str, Sequence[str], None] = "0018_learner_effort_factors"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "activity_versions",
        sa.Column("difficulty", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "ck_activity_versions_difficulty",
        "activity_versions",
        "difficulty IS NULL OR (difficulty >= 1 AND difficulty <= 3)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_activity_versions_difficulty", "activity_versions", type_="check")
    op.drop_column("activity_versions", "difficulty")
