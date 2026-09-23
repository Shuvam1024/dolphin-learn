"""goals, time_budgets, and goal_competencies

Revision ID: 0006_goals_time_budgets
Revises: 0005_curriculum_graph
Create Date: 2026-09-23

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0006_goals_time_budgets"
down_revision: str | None = "0005_curriculum_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("raw_request", sa.Text(), nullable=False),
        sa.Column("normalized_objective", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goals_user_id", "goals", ["user_id"])
    op.create_table(
        "time_budgets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("one_off_minutes", sa.Integer(), nullable=True),
        sa.Column("weekly_minutes_per_day", sa.Integer(), nullable=True),
        sa.Column("horizon_days", sa.Integer(), nullable=True),
        sa.Column("preferred_session_minutes", sa.Integer(), nullable=False),
        sa.CheckConstraint("mode IN ('one_off', 'weekly')", name="ck_time_budgets_mode"),
        sa.CheckConstraint(
            "preferred_session_minutes >= 0",
            name="ck_time_budgets_session_nonnegative",
        ),
        sa.CheckConstraint(
            "("
            "mode = 'one_off' AND one_off_minutes IS NOT NULL AND one_off_minutes >= 0 "
            "AND weekly_minutes_per_day IS NULL AND horizon_days IS NULL"
            ") OR ("
            "mode = 'weekly' AND weekly_minutes_per_day IS NOT NULL "
            "AND weekly_minutes_per_day >= 0 AND horizon_days IS NOT NULL "
            "AND horizon_days > 0 AND one_off_minutes IS NULL"
            ")",
            name="ck_time_budgets_mode_xor",
        ),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("goal_id", name="uq_time_budgets_goal_id"),
    )
    op.create_table(
        "goal_competencies",
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("competency_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["competency_id"], ["competencies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("goal_id", "competency_id"),
    )


def downgrade() -> None:
    op.drop_table("goal_competencies")
    op.drop_table("time_budgets")
    op.drop_index("ix_goals_user_id", table_name="goals")
    op.drop_table("goals")
