"""learner effort factors for calibrated estimates

Revision ID: 0018_learner_effort_factors
Revises: 0017_goal_competency_requirement
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018_learner_effort_factors"
down_revision: Union[str, Sequence[str], None] = "0017_goal_competency_requirement"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learner_effort_factors",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("activity_type", sa.String(length=32), nullable=False),
        sa.Column("factor", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("observations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "factor >= 0.5 AND factor <= 2.0",
            name="ck_learner_effort_factors_clamp",
        ),
        sa.CheckConstraint(
            "observations >= 0",
            name="ck_learner_effort_factors_observations",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "activity_type"),
    )


def downgrade() -> None:
    op.drop_table("learner_effort_factors")
