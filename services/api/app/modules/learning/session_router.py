"""Create, read, and resume a Session Studio session."""

import uuid
from typing import Literal

from app.db import get_db
from app.modules.goals.service import get_owned_goal
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.learning.models import LearningSession
from app.modules.learning.sessions import (
    activity_snapshot,
    apply_event,
    event_count,
    get_owned_session,
    start_session,
)
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, field_validator
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
