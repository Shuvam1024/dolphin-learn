"""Owned goal routes: create, list, get, and update, including time budgets."""

import uuid
from datetime import datetime
from typing import Literal

from app.db import get_db
from app.errors import ApiError
from app.modules.goals.budget import TimeBudgetSpec
from app.modules.goals.diagnostic import NOTE, skip_diagnostic, start_diagnostic, submit_diagnostic
from app.modules.goals.models import Goal, TimeBudget
from app.modules.goals.service import (
    budget_for,
    create_goal,
    get_owned_goal,
    list_goals,
    update_goal,
)
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from sqlalchemy.orm import Session

router = APIRouter(prefix="/goals", tags=["goals"])


def _clean_required(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("must not be empty")
    return cleaned


class GoalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    raw_request: str
    normalized_objective: str | None = None
    time_budget: TimeBudgetSpec | None = None

    @field_validator("title", "raw_request")
    @classmethod
    def _required_text(cls, value: str) -> str:
        return _clean_required(value)

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


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    raw_request: str | None = None
    normalized_objective: str | None = None
    time_budget: TimeBudgetSpec | None = None

    @field_validator("title", "raw_request")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_required(value)

    @field_validator("title")
    @classmethod
    def _title_length(cls, value: str | None) -> str | None:
        if value is not None and len(value) > 200:
            raise ValueError("title must be 200 characters or fewer")
        return value

    @field_validator("normalized_objective")
    @classmethod
    def _objective(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class TimeBudgetOut(BaseModel):
    mode: Literal["one_off", "weekly"]
    one_off_minutes: int | None
    weekly_minutes_per_day: int | None
    horizon_days: int | None
    preferred_session_minutes: int


class GoalOut(BaseModel):
    id: uuid.UUID
    title: str
    raw_request: str
    normalized_objective: str | None
    status: str
    created_at: datetime
    time_budget: TimeBudgetOut | None


def _budget_out(row: TimeBudget | None) -> TimeBudgetOut | None:
    if row is None:
        return None
    mode: Literal["one_off", "weekly"] = "one_off" if row.mode == "one_off" else "weekly"
    return TimeBudgetOut(
        mode=mode,
        one_off_minutes=row.one_off_minutes,
        weekly_minutes_per_day=row.weekly_minutes_per_day,
        horizon_days=row.horizon_days,
        preferred_session_minutes=row.preferred_session_minutes,
    )


def _out(goal: Goal, budget: TimeBudget | None) -> GoalOut:
    return GoalOut(
        id=goal.id,
        title=goal.title,
        raw_request=goal.raw_request,
        normalized_objective=goal.normalized_objective,
        status=goal.status,
        created_at=goal.created_at,
        time_budget=_budget_out(budget),
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
        time_budget=body.time_budget,
    )
    return _out(goal, budget_for(db, goal))


@router.get("", response_model=list[GoalOut])
def get_goals(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[GoalOut]:
    return [_out(goal, budget_for(db, goal)) for goal in list_goals(db, user)]


@router.patch("/{goal_id}", response_model=GoalOut)
def patch_goal(
    goal_id: uuid.UUID,
    body: GoalUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> GoalOut:
    sent = body.model_fields_set
    if not sent:
        raise ApiError("validation_error", "Update needs at least one field", status_code=422)
    goal = update_goal(
        db,
        user,
        goal_id,
        title=body.title,
        raw_request=body.raw_request,
        normalized_objective=body.normalized_objective,
        set_objective="normalized_objective" in sent,
        time_budget=body.time_budget,
    )
    return _out(goal, budget_for(db, goal))


class DiagnosticAnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_version_id: uuid.UUID
    choice: str

    @field_validator("choice")
    @classmethod
    def _choice(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("choice must not be empty")
        return cleaned


class DiagnosticIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["start", "skip", "submit"]
    answers: list[DiagnosticAnswerIn] | None = None

    @model_validator(mode="after")
    def answers_match_action(self) -> "DiagnosticIn":
        if self.action == "submit" and not self.answers:
            raise ValueError("submit needs at least one answer")
        return self


class DiagnosticItemOut(BaseModel):
    activity_version_id: uuid.UUID
    prompt: str


class DiagnosticAttemptOut(BaseModel):
    id: uuid.UUID
    activity_version_id: uuid.UUID


class DiagnosticOut(BaseModel):
    status: Literal["items", "skipped", "recorded"]
    mastery_claimed: bool
    note: str
    items: list[DiagnosticItemOut]
    attempts: list[DiagnosticAttemptOut]


@router.post("/{goal_id}/diagnostic", response_model=DiagnosticOut)
def post_diagnostic(
    goal_id: uuid.UUID,
    body: DiagnosticIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> DiagnosticOut:
    goal = get_owned_goal(db, user, goal_id)
    if body.action == "start":
        items = start_diagnostic(db, goal)
        return DiagnosticOut(
            status="items",
            mastery_claimed=False,
            note=NOTE,
            items=[
                DiagnosticItemOut(activity_version_id=item.id, prompt=item.prompt) for item in items
            ],
            attempts=[],
        )
    if body.action == "skip":
        skip_diagnostic(db, user, goal)
        return DiagnosticOut(
            status="skipped",
            mastery_claimed=False,
            note=NOTE,
            items=[],
            attempts=[],
        )
    assert body.answers is not None
    _run, attempts = submit_diagnostic(
        db,
        user,
        goal,
        [(answer.activity_version_id, answer.choice) for answer in body.answers],
    )
    return DiagnosticOut(
        status="recorded",
        mastery_claimed=False,
        note=NOTE,
        items=[],
        attempts=[
            DiagnosticAttemptOut(id=attempt.id, activity_version_id=attempt.activity_version_id)
            for attempt in attempts
        ],
    )


@router.get("/{goal_id}", response_model=GoalOut)
def get_goal(
    goal_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> GoalOut:
    goal = get_owned_goal(db, user, goal_id)
    return _out(goal, budget_for(db, goal))
