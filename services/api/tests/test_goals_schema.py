"""S15: a goal belongs to a user, and a budget cannot contain negative minutes."""

import uuid

import pytest
from app.db import SessionLocal
from app.modules.goals.budget import TimeBudgetSpec
from app.modules.goals.models import Goal, TimeBudget
from app.modules.identity.models import User
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError


def test_validator_rejects_negative_minutes() -> None:
    with pytest.raises(ValidationError):
        TimeBudgetSpec(mode="one_off", one_off_minutes=-1, preferred_session_minutes=25)
    with pytest.raises(ValidationError):
        TimeBudgetSpec(
            mode="weekly",
            weekly_minutes_per_day=-5,
            horizon_days=14,
            preferred_session_minutes=25,
        )


def test_validator_accepts_quick_learn_and_weekly_window() -> None:
    one_off = TimeBudgetSpec(mode="one_off", one_off_minutes=120, preferred_session_minutes=30)
    weekly = TimeBudgetSpec(
        mode="weekly",
        weekly_minutes_per_day=30,
        horizon_days=14,
        preferred_session_minutes=30,
    )
    assert one_off.one_off_minutes == 120
    assert weekly.horizon_days == 14


def test_goal_requires_user_and_budget_rejects_negative_in_database() -> None:
    db = SessionLocal()
    try:
        db.add(Goal(title="Python", raw_request="Learn Python"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        user = User(auth_subject=f"dev|goals-{uuid.uuid4().hex[:8]}@example.com", email=None)
        db.add(user)
        db.commit()
        goal = Goal(user_id=user.id, title="Python", raw_request="Learn Python in two hours")
        db.add(goal)
        db.commit()

        db.add(
            TimeBudget(
                goal_id=goal.id,
                mode="one_off",
                one_off_minutes=-10,
                preferred_session_minutes=25,
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        spec = TimeBudgetSpec(mode="one_off", one_off_minutes=120, preferred_session_minutes=30)
        db.add(
            TimeBudget(
                goal_id=goal.id,
                mode=spec.mode,
                one_off_minutes=spec.one_off_minutes,
                preferred_session_minutes=spec.preferred_session_minutes,
            )
        )
        db.commit()
    finally:
        db.close()
