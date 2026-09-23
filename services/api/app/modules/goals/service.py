"""Create and read goals that belong to the authenticated learner."""

import uuid

from app.errors import ApiError
from app.modules.goals.models import Goal
from app.modules.identity.models import User
from sqlalchemy import select
from sqlalchemy.orm import Session


def create_goal(
    db: Session,
    user: User,
    *,
    title: str,
    raw_request: str,
    normalized_objective: str | None,
) -> Goal:
    goal = Goal(
        user_id=user.id,
        title=title,
        raw_request=raw_request,
        normalized_objective=normalized_objective,
        status="active",
    )
    db.add(goal)
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
