"""Persisted Session Studio sessions. Events are append-only and idempotent."""

import uuid
from datetime import datetime, timezone

from app.errors import ApiError
from app.modules.goals.models import Goal
from app.modules.identity.models import User
from app.modules.learning.accept import latest_accepted
from app.modules.learning.models import LearningSession, PlanActivity, SessionEvent
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
