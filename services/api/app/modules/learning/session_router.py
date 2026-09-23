"""Create, read, and resume a Session Studio session."""

import uuid
from typing import Literal

from app.db import get_db
from app.modules.goals.service import get_owned_goal
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.learning.grading import eligible_for_independent_evidence
from app.modules.learning.models import Evaluation, LearningSession
from app.modules.learning.sessions import (
    activity_snapshot,
    apply_event,
    event_count,
    get_owned_session,
    record_help,
    start_session,
    submit_attempt,
)
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: uuid.UUID


class SessionEventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_event_id: str
    event_type: Literal["pause", "resume", "progress"]
    payload: dict[str, str] = {}

    @field_validator("client_event_id")
    @classmethod
    def _event_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned or len(cleaned) > 64:
            raise ValueError("client_event_id must be 1 to 64 characters")
        return cleaned


class SessionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: SessionEventIn


class ActivityOut(BaseModel):
    activity_type: str
    title: str
    prompt: str
    body: str
    mode: Literal["guided"]
    recorded_choice: str = ""
    help: str = "none"
    revealed_choice: str = ""
    outcome: str = ""
    attempt_assistance: str = ""


class SessionOut(BaseModel):
    id: uuid.UUID
    status: str
    goal_id: uuid.UUID | None = None
    plan_activity_id: uuid.UUID | None
    event_count: int
    applied: bool
    activity: ActivityOut | None = None


def _out(
    row: LearningSession,
    db: Session,
    *,
    applied: bool,
    goal_id: uuid.UUID | None = None,
) -> SessionOut:
    return SessionOut(
        id=row.id,
        status=row.status,
        goal_id=goal_id,
        plan_activity_id=row.plan_activity_id,
        event_count=event_count(db, row.id),
        applied=applied,
        activity=ActivityOut.model_validate(snap) if (snap := activity_snapshot(db, row)) else None,
    )


@router.post("", response_model=SessionOut, status_code=201)
def post_session(
    body: SessionCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SessionOut:
    goal = get_owned_goal(db, user, body.goal_id)
    row = start_session(db, user, goal)
    return _out(row, db, applied=True, goal_id=goal.id)


@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SessionOut:
    row = get_owned_session(db, user, session_id)
    return _out(row, db, applied=True)


@router.patch("/{session_id}", response_model=SessionOut)
def patch_session(
    session_id: uuid.UUID,
    body: SessionPatch,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SessionOut:
    row, applied = apply_event(
        db,
        user,
        session_id,
        client_event_id=body.event.client_event_id,
        event_type=body.event.event_type,
        payload=body.event.payload,
    )
    return _out(row, db, applied=applied)


class AttemptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str
    choice: str

    @field_validator("idempotency_key")
    @classmethod
    def _key(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned or len(cleaned) > 64:
            raise ValueError("idempotency_key must be 1 to 64 characters")
        return cleaned

    @field_validator("choice")
    @classmethod
    def _choice(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"a", "b", "c"}:
            raise ValueError("choice must be a, b, or c")
        return cleaned


class AttemptOut(BaseModel):
    id: uuid.UUID
    activity_version_id: uuid.UUID
    choice: str
    assistance: str
    prompt: str
    outcome: str
    eligible_for_independent_evidence: bool
    created: bool


@router.post("/{session_id}/attempts", response_model=AttemptOut)
def post_attempt(
    session_id: uuid.UUID,
    body: AttemptIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AttemptOut:
    attempt, created = submit_attempt(
        db,
        user,
        session_id,
        idempotency_key=body.idempotency_key,
        choice=body.choice,
    )
    evaluation = db.scalar(select(Evaluation).where(Evaluation.attempt_id == attempt.id))
    outcome = evaluation.outcome if evaluation is not None else ""
    assistance = str(attempt.response.get("assistance", "independent"))
    return AttemptOut(
        id=attempt.id,
        activity_version_id=attempt.activity_version_id,
        choice=str(attempt.response.get("choice", "")),
        assistance=assistance,
        prompt=str(attempt.response.get("prompt", "")),
        outcome=outcome,
        eligible_for_independent_evidence=eligible_for_independent_evidence(assistance, outcome),
        created=created,
    )


class HelpIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["guided", "challenge"] = "guided"


class HelpOut(BaseModel):
    kind: str
    message: str
    revealed_choice: str


@router.post("/{session_id}/hint", response_model=HelpOut)
def post_hint(
    session_id: uuid.UUID,
    body: HelpIn | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> HelpOut:
    mode = "guided" if body is None else body.mode
    return HelpOut.model_validate(record_help(db, user, session_id, kind="hint", mode=mode))


@router.post("/{session_id}/solution", response_model=HelpOut)
def post_solution(
    session_id: uuid.UUID,
    body: HelpIn | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> HelpOut:
    mode = "guided" if body is None else body.mode
    return HelpOut.model_validate(record_help(db, user, session_id, kind="solution", mode=mode))
