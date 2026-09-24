"""competencies and lessons may be owned by a learner for the General route

Revision ID: 0016_owned_competencies
Revises: 0015_goal_status
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016_owned_competencies"
down_revision: Union[str, Sequence[str], None] = "0015_goal_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "competencies",
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "competencies",
        sa.Column("goal_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_competencies_owner_user_id",
        "competencies",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_competencies_goal_id",
        "competencies",
        "goals",
        ["goal_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_competencies_owner_user_id", "competencies", ["owner_user_id"])
    op.create_index("ix_competencies_goal_id", "competencies", ["goal_id"])

    op.add_column(
        "lessons",
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_lessons_owner_user_id",
        "lessons",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_lessons_owner_user_id", "lessons", ["owner_user_id"])


def downgrade() -> None:
    op.drop_index("ix_lessons_owner_user_id", table_name="lessons")
    op.drop_constraint("fk_lessons_owner_user_id", "lessons", type_="foreignkey")
    op.drop_column("lessons", "owner_user_id")

    op.drop_index("ix_competencies_goal_id", table_name="competencies")
    op.drop_index("ix_competencies_owner_user_id", table_name="competencies")
    op.drop_constraint("fk_competencies_goal_id", "competencies", type_="foreignkey")
    op.drop_constraint("fk_competencies_owner_user_id", "competencies", type_="foreignkey")
    op.drop_column("competencies", "goal_id")
    op.drop_column("competencies", "owner_user_id")
