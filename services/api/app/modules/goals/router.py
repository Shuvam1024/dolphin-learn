"""Owned goal routes: create, list, and get. Budgets arrive in a later step."""

import uuid
from datetime import datetime

from app.db import get_db
from app.modules.goals.models import Goal
from app.modules.goals.service import create_goal, get_owned_goal, list_goals
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

router = APIRouter(prefix="/goals", tags=["goals"])


class GoalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    raw_request: str
    normalized_objective: str | None = None

    @field_validator("title", "raw_request")
    @classmethod
    def _required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("title")
    @classmethod
    def _title_length(cls, value: str) -> str:
        if len(value) > 200:
            raise ValueError("title must be 200 characters or fewer")
        return value

    @field_validator("normalized_objective")
    @classmethod
    def _objective(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class GoalOut(BaseModel):
    id: uuid.UUID
    title: str
    raw_request: str
    normalized_objective: str | None
    status: str
    created_at: datetime


def _out(goal: Goal) -> GoalOut:
    return GoalOut(
        id=goal.id,
        title=goal.title,
        raw_request=goal.raw_request,
        normalized_objective=goal.normalized_objective,
        status=goal.status,
        created_at=goal.created_at,
    )


@router.post("", response_model=GoalOut, status_code=201)
def post_goal(
    body: GoalIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> GoalOut:
    goal = create_goal(
        db,
        user,
        title=body.title,
        raw_request=body.raw_request,
        normalized_objective=body.normalized_objective,
    )
    return _out(goal)


@router.get("", response_model=list[GoalOut])
def get_goals(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[GoalOut]:
    return [_out(goal) for goal in list_goals(db, user)]


@router.get("/{goal_id}", response_model=GoalOut)
def get_goal(
    goal_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> GoalOut:
    return _out(get_owned_goal(db, user, goal_id))
