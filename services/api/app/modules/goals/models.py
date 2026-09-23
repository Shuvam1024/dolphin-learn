"""Owned goals and the minutes the learner actually has."""

import uuid
from datetime import datetime

from app.db import Base
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    raw_request: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TimeBudget(Base):
    """One mode per goal: a single block of minutes, or a weekly window. Not both."""

    __tablename__ = "time_budgets"
    __table_args__ = (
        CheckConstraint("mode IN ('one_off', 'weekly')", name="ck_time_budgets_mode"),
        CheckConstraint(
            "preferred_session_minutes >= 0",
            name="ck_time_budgets_session_nonnegative",
        ),
        CheckConstraint(
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
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    one_off_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weekly_minutes_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    horizon_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_session_minutes: Mapped[int] = mapped_column(Integer, nullable=False)


class GoalCompetency(Base):
    __tablename__ = "goal_competencies"

    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True
    )
