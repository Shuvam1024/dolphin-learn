"""Persisted Session Studio sessions. Events are append-only and idempotent."""

import uuid
from datetime import datetime, timezone

from app.errors import ApiError
from app.modules.goals.models import Goal
from app.modules.identity.models import User
from app.modules.learning.accept import latest_accepted
from app.modules.learning.models import (
    ActivityVersion,
    Attempt,
    LearningSession,
    Lesson,
    PlanActivity,
    SessionEvent,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _first_activity(db: Session, user: User, goal: Goal) -> PlanActivity:
    version = latest_accepted(db, user, goal)
    if version is None:
        raise ApiError(
            "validation_error",
            "Accept a plan before starting a session",
            status_code=422,
        )
    activity = db.scalar(
        select(PlanActivity)
        .where(PlanActivity.plan_version_id == version.id)
        .order_by(PlanActivity.position)
    )
    if activity is None:
        raise ApiError(
            "validation_error",
            "The accepted plan has no activities to start",
            status_code=422,
        )
    return activity


def start_session(db: Session, user: User, goal: Goal) -> LearningSession:
    activity = _first_activity(db, user, goal)
    row = LearningSession(
        user_id=user.id,
        plan_activity_id=activity.id,
        status="active",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_owned_session(db: Session, user: User, session_id: uuid.UUID) -> LearningSession:
    row = db.scalar(
        select(LearningSession).where(
            LearningSession.id == session_id,
            LearningSession.user_id == user.id,
        )
    )
    if row is None:
        raise ApiError("not_found", "Session not found", status_code=404)
    return row


def activity_snapshot(db: Session, row: LearningSession) -> dict[str, str] | None:
    """Reading content for the current activity. Answer keys stay on the server."""
    if row.plan_activity_id is None:
        return None
    plan = db.get(PlanActivity, row.plan_activity_id)
    if plan is None or plan.activity_version_id is None:
        return None
    activity = db.get(ActivityVersion, plan.activity_version_id)
    if activity is None:
        return None
    lesson = db.get(Lesson, activity.lesson_id)
    latest = db.scalar(
        select(Attempt)
        .where(Attempt.session_id == row.id, Attempt.activity_version_id == activity.id)
        .order_by(Attempt.submitted_at.desc())
    )
    recorded = ""
    if latest is not None:
        recorded = str(latest.response.get("choice", ""))
    return {
        "activity_type": activity.activity_type,
        "title": lesson.title if lesson is not None else plan.title,
        "prompt": activity.prompt,
        "body": lesson.body_markdown if lesson is not None else "",
        "mode": "guided",
        "recorded_choice": recorded,
    }


def submit_attempt(
    db: Session,
    user: User,
    session_id: uuid.UUID,
    *,
    idempotency_key: str,
    choice: str,
) -> tuple[Attempt, bool]:
    """Store an immutable answer snapshot. The same key returns the first row."""
    session = get_owned_session(db, user, session_id)
    existing = db.scalar(
        select(Attempt).where(
            Attempt.session_id == session.id,
            Attempt.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing, False
    if session.plan_activity_id is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    plan = db.get(PlanActivity, session.plan_activity_id)
    if plan is None or plan.activity_version_id is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    activity = db.get(ActivityVersion, plan.activity_version_id)
    if activity is None or activity.activity_type != "objective":
        raise ApiError("validation_error", "This activity is not a question", status_code=422)
    attempt = Attempt(
        user_id=user.id,
        activity_version_id=activity.id,
        session_id=session.id,
        idempotency_key=idempotency_key,
        response={
            "choice": choice,
            "prompt": activity.prompt,
            "assistance": "independent",
        },
    )
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Attempt).where(
                Attempt.session_id == session.id,
                Attempt.idempotency_key == idempotency_key,
            )
        )
        if existing is None:
            raise
        return existing, False
    db.refresh(attempt)
    return attempt, True


def event_count(db: Session, session_id: uuid.UUID) -> int:
    count = db.scalar(
        select(func.count()).select_from(SessionEvent).where(SessionEvent.session_id == session_id)
    )
    return int(count or 0)


def _activity_on_same_plan(
    db: Session,
    session: LearningSession,
    activity_id: uuid.UUID,
) -> PlanActivity:
    current = db.get(PlanActivity, session.plan_activity_id) if session.plan_activity_id else None
    if current is None:
        raise ApiError("validation_error", "Session is not on a plan activity", status_code=422)
    target = db.get(PlanActivity, activity_id)
    if target is None or target.plan_version_id != current.plan_version_id:
        raise ApiError("validation_error", "That activity is not on this plan", status_code=422)
    return target


def apply_event(
    db: Session,
    user: User,
    session_id: uuid.UUID,
    *,
    client_event_id: str,
    event_type: str,
    payload: dict[str, str],
) -> tuple[LearningSession, bool]:
    session = get_owned_session(db, user, session_id)
    existing = db.scalar(
        select(SessionEvent).where(
            SessionEvent.session_id == session.id,
            SessionEvent.client_event_id == client_event_id,
        )
    )
    if existing is not None:
        return session, False

    if event_type == "progress":
        raw = payload.get("plan_activity_id", "")
        try:
            activity_id = uuid.UUID(raw)
        except ValueError as exc:
            raise ApiError(
                "validation_error",
                "progress needs a plan_activity_id",
                status_code=422,
            ) from exc
        _activity_on_same_plan(db, session, activity_id)
        session.plan_activity_id = activity_id
    elif event_type == "pause":
        session.status = "paused"
    elif event_type == "resume":
        session.status = "active"
    else:
        raise ApiError("validation_error", "Unknown session event", status_code=422)

    session.updated_at = datetime.now(timezone.utc)
    db.add(
        SessionEvent(
            session_id=session.id,
            client_event_id=client_event_id,
            event_type=event_type,
            payload=payload,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        session = get_owned_session(db, user, session_id)
        return session, False
    db.refresh(session)
    return session, True
