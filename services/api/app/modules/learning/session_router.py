"""Create, read, and resume a Session Studio session."""

import uuid
from typing import Literal

from app.db import get_db
from app.modules.goals.service import get_owned_goal
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.learning.evidence import move_to_unseen_question
from app.modules.learning.free_recall import submit_self_rating
from app.modules.learning.grading import eligible_for_independent_evidence
from app.modules.learning.models import Evaluation, LearningSession
from app.modules.learning.sessions import (
    activity_snapshot,
    advance_session,
    apply_event,
    event_count,
    get_owned_session,
    record_help,
    start_session,
    submit_attempt,
)
from app.modules.learning.study_time import session_active_minutes
from app.modules.learning.summary import build_summary, finish_session
from app.modules.learning.tutor import request_explain
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: uuid.UUID
    target_minutes: int | None = None

    @field_validator("target_minutes")
    @classmethod
    def _target(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 5 or value > 180:
            raise ValueError("target_minutes must be between 5 and 180")
        return value


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


class SummaryItemOut(BaseModel):
    competency_key: str
    competency_name: str = ""
    lesson_title: str = ""
    title: str = ""
    reason: str = ""
    attempt_id: str = ""
    outcome: str = ""
    choice: str = ""
    note: str = ""
    source: str = ""
    rating: str = ""


class SummaryOut(BaseModel):
    topics: list[SummaryItemOut]
    independent_attempts: list[SummaryItemOut]
    unresolved: list[SummaryItemOut]
    suggested_review: list[SummaryItemOut]
    watch_out_for: list[SummaryItemOut] = []
    showed_on_your_own: list[SummaryItemOut] = []
    practiced_with_help: list[SummaryItemOut] = []
    self_reported: list[SummaryItemOut] = []
    next_review: dict[str, object] | None = None
    minutes_studied: int = 0
    next_step: dict[str, str] | None = None
    note: str


class SessionOut(BaseModel):
    id: uuid.UUID
    status: str
    goal_id: uuid.UUID | None = None
    plan_activity_id: uuid.UUID | None
    event_count: int
    active_minutes: int
    applied: bool
    activity: ActivityOut | None = None
    summary: SummaryOut | None = None
    target_minutes: int = 0
    goal: dict[str, str] | None = None
    lesson: dict[str, str] | None = None
    position: int = 0
    total: int = 0
    remaining_estimate: dict[str, int] | None = None
    studio_activity: dict[str, object] | None = None
    actions: dict[str, object] | None = None
    tutor: dict[str, object] | None = None


def _out(
    row: LearningSession,
    db: Session,
    *,
    applied: bool,
    goal_id: uuid.UUID | None = None,
    user: User | None = None,
) -> SessionOut:
    from app.modules.learning.studio_view import build_studio

    studio = build_studio(db, user, row) if user is not None else None
    resolved_goal = goal_id
    if resolved_goal is None and studio and studio["goal"]["id"]:
        resolved_goal = uuid.UUID(str(studio["goal"]["id"]))
    return SessionOut(
        id=row.id,
        status=row.status,
        goal_id=resolved_goal,
        plan_activity_id=row.plan_activity_id,
        event_count=event_count(db, row.id),
        active_minutes=session_active_minutes(db, row),
        applied=applied,
        activity=ActivityOut.model_validate(snap) if (snap := activity_snapshot(db, row)) else None,
        summary=(
            SummaryOut.model_validate(build_summary(db, row)) if row.status == "finished" else None
        ),
        target_minutes=int(studio["target_minutes"]) if studio else 0,
        goal=studio["goal"] if studio else None,
        lesson=studio["lesson"] if studio else None,
        position=int(studio["position"]) if studio else 0,
        total=int(studio["total"]) if studio else 0,
        remaining_estimate=studio["remaining_estimate"] if studio else None,
        studio_activity=studio["activity"] if studio else None,
        actions=studio["actions"] if studio else None,
        tutor=studio["tutor"] if studio else None,
    )


@router.post("", response_model=SessionOut, status_code=201)
def post_session(
    body: SessionCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SessionOut:
    goal = get_owned_goal(db, user, body.goal_id)
    row = start_session(db, user, goal, target_minutes=body.target_minutes)
    return _out(row, db, applied=True, goal_id=goal.id, user=user)


@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SessionOut:
    row = get_owned_session(db, user, session_id)
    return _out(row, db, applied=True, user=user)


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
    return _out(row, db, applied=applied, user=user)


class AttemptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str
    choice: str | None = None
    text: str | None = None
    value: str | None = None

    @field_validator("idempotency_key")
    @classmethod
    def _key(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned or len(cleaned) > 64:
            raise ValueError("idempotency_key must be 1 to 64 characters")
        return cleaned

    @field_validator("choice")
    @classmethod
    def _choice(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in {"a", "b", "c"}:
            raise ValueError("choice must be a, b, or c")
        return cleaned


class AttemptOut(BaseModel):
    id: uuid.UUID
    activity_version_id: uuid.UUID
    choice: str
    text: str = ""
    value: str = ""
    assistance: str
    prompt: str
    outcome: str
    eligible_for_independent_evidence: bool
    created: bool
    misconception_note: str = ""
    misconception_source: str = ""


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
        text=body.text,
        value=body.value,
    )
    evaluation = db.scalar(select(Evaluation).where(Evaluation.attempt_id == attempt.id))
    outcome = evaluation.outcome if evaluation is not None else ""
    assistance = str(attempt.response.get("assistance", "independent"))
    note = ""
    note_source = ""
    if evaluation is not None and evaluation.feedback_json:
        note = str(evaluation.feedback_json.get("misconception_note", "") or "")
        note_source = str(evaluation.feedback_json.get("misconception_source", "") or "")
    return AttemptOut(
        id=attempt.id,
        activity_version_id=attempt.activity_version_id,
        choice=str(attempt.response.get("choice", "")),
        text=str(attempt.response.get("text", "")),
        value=str(attempt.response.get("value", "")),
        assistance=assistance,
        prompt=str(attempt.response.get("prompt", "")),
        outcome=outcome,
        eligible_for_independent_evidence=eligible_for_independent_evidence(assistance, outcome),
        created=created,
        misconception_note=note,
        misconception_source=note_source,
    )


class HelpIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["guided", "challenge"] = "guided"


class HelpOut(BaseModel):
    kind: str
    message: str
    revealed_choice: str
    hint_source: str = "seed"


class ExplainOut(BaseModel):
    explanation_markdown: str
    analogy_used: bool = False
    hint_count: int = 0


@router.post("/{session_id}/finish", response_model=SessionOut)
def post_finish(
    session_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SessionOut:
    row, _summary = finish_session(db, user, session_id)
    return _out(row, db, applied=True, user=user)


@router.post("/{session_id}/advance", response_model=SessionOut)
def post_advance(
    session_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SessionOut:
    row = advance_session(db, user, session_id)
    return _out(row, db, applied=True, user=user)


@router.post("/{session_id}/independent-check", response_model=SessionOut)
def post_independent_check(
    session_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SessionOut:
    row = move_to_unseen_question(db, user, session_id)
    return _out(row, db, applied=True, user=user)


@router.post("/{session_id}/hint", response_model=HelpOut)
def post_hint(
    session_id: uuid.UUID,
    body: HelpIn | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> HelpOut:
    mode = "guided" if body is None else body.mode
    return HelpOut.model_validate(record_help(db, user, session_id, kind="hint", mode=mode))


@router.post("/{session_id}/explain", response_model=ExplainOut)
def post_explain(
    session_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ExplainOut:
    return ExplainOut.model_validate(request_explain(db, user, session_id))


class SelfRateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: Literal["got_it", "partly", "not_yet"]


class SelfRateOut(BaseModel):
    rating: str
    outcome: str
    facet: str


@router.post("/{session_id}/self-rate", response_model=SelfRateOut)
def post_self_rate(
    session_id: uuid.UUID,
    body: SelfRateIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SelfRateOut:
    return SelfRateOut.model_validate(submit_self_rating(db, user, session_id, rating=body.rating))


@router.post("/{session_id}/solution", response_model=HelpOut)
def post_solution(
    session_id: uuid.UUID,
    body: HelpIn | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> HelpOut:
    mode = "guided" if body is None else body.mode
    return HelpOut.model_validate(record_help(db, user, session_id, kind="solution", mode=mode))
