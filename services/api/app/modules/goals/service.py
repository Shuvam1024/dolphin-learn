"""Create and read goals that belong to the authenticated learner."""

import uuid

from app.errors import ApiError
from app.modules.curriculum.models import Domain
from app.modules.goals.budget import TimeBudgetSpec
from app.modules.goals.models import Goal, TimeBudget
from app.modules.identity.models import User
from sqlalchemy import select
from sqlalchemy.orm import Session


def _budget_values(spec: TimeBudgetSpec) -> dict[str, object]:
    if spec.mode == "one_off":
        return {
            "mode": "one_off",
            "one_off_minutes": spec.one_off_minutes,
            "weekly_minutes_per_day": None,
            "horizon_days": None,
            "preferred_session_minutes": spec.preferred_session_minutes,
        }
    return {
        "mode": "weekly",
        "one_off_minutes": None,
        "weekly_minutes_per_day": spec.weekly_minutes_per_day,
        "horizon_days": spec.horizon_days,
        "preferred_session_minutes": spec.preferred_session_minutes,
    }


def upsert_budget(db: Session, goal: Goal, spec: TimeBudgetSpec) -> TimeBudget:
    row = db.scalar(select(TimeBudget).where(TimeBudget.goal_id == goal.id))
    values = _budget_values(spec)
    if row is None:
        row = TimeBudget(goal_id=goal.id, **values)
        db.add(row)
        return row
    for key, value in values.items():
        setattr(row, key, value)
    return row


def budget_for(db: Session, goal: Goal) -> TimeBudget | None:
    return db.scalar(select(TimeBudget).where(TimeBudget.goal_id == goal.id))


def require_domain(db: Session, domain_key: str) -> str:
    key = domain_key.strip()
    if not key:
        raise ApiError(
            "validation_error",
            "Choose a subject we can teach today",
            status_code=422,
        )
    domain = db.scalar(select(Domain).where(Domain.key == key))
    if domain is None:
        raise ApiError(
            "validation_error",
            "We do not have lessons for that subject yet",
            status_code=422,
        )
    return domain.key


def create_goal(
    db: Session,
    user: User,
    *,
    title: str,
    raw_request: str,
    domain_key: str,
    normalized_objective: str | None,
    time_budget: TimeBudgetSpec | None,
    priority: str = "understand",
) -> Goal:
    goal = Goal(
        user_id=user.id,
        title=title,
        raw_request=raw_request,
        domain_key=require_domain(db, domain_key),
        normalized_objective=normalized_objective,
        priority=priority,
        status="active",
    )
    db.add(goal)
    db.flush()
    if time_budget is not None:
        upsert_budget(db, goal, time_budget)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(
    db: Session,
    user: User,
    goal_id: uuid.UUID,
    *,
    title: str | None,
    raw_request: str | None,
    domain_key: str | None,
    set_domain: bool,
    normalized_objective: str | None,
    set_objective: bool,
    time_budget: TimeBudgetSpec | None,
    priority: str | None = None,
    set_priority: bool = False,
    status: str | None = None,
    set_status: bool = False,
) -> Goal:
    goal = get_owned_goal(db, user, goal_id)
    if title is not None:
        goal.title = title
    if raw_request is not None:
        goal.raw_request = raw_request
    if set_domain:
        if domain_key is None:
            raise ApiError(
                "validation_error",
                "Choose a subject we can teach today",
                status_code=422,
            )
        goal.domain_key = require_domain(db, domain_key)
    if set_objective:
        goal.normalized_objective = normalized_objective
    if set_priority:
        if priority is None:
            raise ApiError(
                "validation_error",
                "Choose how you want to focus this goal",
                status_code=422,
            )
        goal.priority = priority
    if set_status:
        if status not in {"active", "paused", "archived"}:
            raise ApiError(
                "validation_error",
                "Status must be active, paused, or archived",
                status_code=422,
            )
        goal.status = status
    if time_budget is not None:
        upsert_budget(db, goal, time_budget)
    db.commit()
    db.refresh(goal)
    return goal


def list_goals(db: Session, user: User) -> list[Goal]:
    rows = db.scalars(
        select(Goal).where(Goal.user_id == user.id).order_by(Goal.created_at.desc(), Goal.id)
    )
    return list(rows)


def get_owned_goal(db: Session, user: User, goal_id: uuid.UUID) -> Goal:
    """Missing and someone else's goal look the same: not found."""
    goal = db.scalar(select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id))
    if goal is None:
        raise ApiError("not_found", "Goal not found", status_code=404)
    return goal
