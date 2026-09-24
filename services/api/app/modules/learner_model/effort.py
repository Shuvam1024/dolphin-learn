"""Per-learner effort calibration from measured active minutes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.modules.identity.models import User
from app.modules.learning.models import ActivityVersion, PlanActivity
from sqlalchemy import ForeignKey, Integer, String, DateTime, Float, func
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db import Base

ALPHA = 0.3
MIN_OBSERVATIONS = 3
FACTOR_MIN = 0.5
FACTOR_MAX = 2.0


class LearnerEffortFactor(Base):
    __tablename__ = "learner_effort_factors"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    activity_type: Mapped[str] = mapped_column(String(32), primary_key=True)
    factor: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    observations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


def clamp_factor(value: float) -> float:
    return max(FACTOR_MIN, min(FACTOR_MAX, value))


def record_observation(
    db: Session,
    user: User,
    activity_type: str,
    *,
    observed_minutes: float,
    declared_low: float,
) -> LearnerEffortFactor:
    """Update EMA of observed / declared_low for this activity type."""
    if declared_low <= 0:
        declared_low = 1.0
    ratio = float(observed_minutes) / float(declared_low)
    row = db.get(LearnerEffortFactor, (user.id, activity_type))
    if row is None:
        row = LearnerEffortFactor(
            user_id=user.id,
            activity_type=activity_type,
            factor=clamp_factor(ratio),
            observations=1,
            updated_at=datetime.now(timezone.utc),
        )
        db.add(row)
    else:
        row.observations += 1
        row.factor = clamp_factor((1.0 - ALPHA) * float(row.factor) + ALPHA * ratio)
        row.updated_at = datetime.now(timezone.utc)
    db.flush()
    db.refresh(row)
    return row


def factor_for(
    db: Session,
    user: User,
    activity_type: str,
) -> float:
    """Return the calibrated factor, or 1.0 until enough observations."""
    row = db.get(LearnerEffortFactor, (user.id, activity_type))
    if row is None or row.observations < MIN_OBSERVATIONS:
        return 1.0
    return clamp_factor(float(row.factor))


def scale_effort(
    db: Session,
    user: User | None,
    activity_type: str,
    low: int,
    high: int,
) -> tuple[int, int]:
    if user is None:
        return low, high
    factor = factor_for(db, user, activity_type)
    if factor == 1.0:
        return low, high
    scaled_low = max(1, int(round(low * factor)))
    scaled_high = max(scaled_low, int(round(high * factor)))
    return scaled_low, scaled_high


def calibration_note(db: Session, user: User) -> str:
    """One sentence shown once when any factor is active."""
    from sqlalchemy import select

    rows = list(
        db.scalars(
            select(LearnerEffortFactor).where(
                LearnerEffortFactor.user_id == user.id,
                LearnerEffortFactor.observations >= MIN_OBSERVATIONS,
            )
        )
    )
    if not rows:
        return ""
    return "estimates adjusted from your last sessions"


def record_activity_minutes(
    db: Session,
    user: User,
    plan_activity: PlanActivity,
    *,
    observed_minutes: float,
) -> None:
    if plan_activity.activity_version_id is None:
        return
    activity = db.get(ActivityVersion, plan_activity.activity_version_id)
    if activity is None:
        return
    declared = max(1, int(activity.effort_minutes_low or 1))
    record_observation(
        db,
        user,
        activity.activity_type,
        observed_minutes=max(0.0, float(observed_minutes)),
        declared_low=float(declared),
    )
