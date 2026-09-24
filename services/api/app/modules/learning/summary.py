"""Honest end-of-session summary built from stored attempts. No celebration copy."""

import uuid
from datetime import datetime, timezone

from app.modules.curriculum.models import Competency
from app.modules.identity.models import User
from app.modules.learning.models import (
    ActivityVersion,
    Attempt,
    Evaluation,
    LearningSession,
    Lesson,
    PlanActivity,
    SessionEvent,
)
from sqlalchemy import select
from sqlalchemy.orm import Session


def _plan_version_id(db: Session, session: LearningSession):
    if session.plan_activity_id is None:
        return None
    plan = db.get(PlanActivity, session.plan_activity_id)
    if plan is None:
        return None
    return plan.plan_version_id


def build_summary(db: Session, session: LearningSession) -> dict[str, object]:
    rows = db.execute(
        select(Attempt, Evaluation, Competency.key, Competency.name, Lesson.title)
        .join(Evaluation, Evaluation.attempt_id == Attempt.id)
        .join(ActivityVersion, Attempt.activity_version_id == ActivityVersion.id)
        .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
        .join(Competency, Lesson.competency_id == Competency.id)
        .where(Attempt.session_id == session.id)
        .order_by(Attempt.submitted_at, Attempt.id)
    ).all()

    topics: list[dict[str, str]] = []
    seen_topics: set[str] = set()
    independent: list[dict[str, str]] = []
    demonstrated: set[str] = set()
    names: dict[str, str] = {}
    for attempt, evaluation, key, name, title in rows:
        names[key] = name
        if key not in seen_topics:
            seen_topics.add(key)
            topics.append(
                {
                    "competency_key": key,
                    "competency_name": name,
                    "lesson_title": title,
                    "title": title,
                }
            )
        if evaluation.assistance == "independent":
            independent.append(
                {
                    "attempt_id": str(attempt.id),
                    "competency_key": key,
                    "competency_name": name,
                    "outcome": evaluation.outcome,
                    "choice": str(attempt.response.get("choice", "")),
                }
            )
            if evaluation.outcome == "correct":
                demonstrated.add(key)

    unresolved: list[dict[str, str]] = []
    version_id = _plan_version_id(db, session)
    if version_id is not None:
        planned = db.execute(
            select(PlanActivity, ActivityVersion, Competency.key, Competency.name)
            .join(ActivityVersion, PlanActivity.activity_version_id == ActivityVersion.id)
            .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
            .join(Competency, Lesson.competency_id == Competency.id)
            .where(
                PlanActivity.plan_version_id == version_id,
                ActivityVersion.activity_type == "objective",
            )
            .order_by(PlanActivity.position)
        ).all()
        solved_activities = {
            attempt.activity_version_id
            for attempt, evaluation, _key, _name, _title in rows
            if evaluation.assistance == "independent" and evaluation.outcome == "correct"
        }
        for plan, activity, key, name in planned:
            if activity.id in solved_activities:
                continue
            unresolved.append(
                {
                    "title": plan.title,
                    "competency_key": key,
                    "competency_name": name,
                    "reason": "No independent correct attempt in this session",
                }
            )

    suggested = [
        {
            "competency_key": key,
            "competency_name": names.get(key, key),
            "reason": "Independent success in this session. Not retention.",
        }
        for key in sorted(demonstrated)
    ]

    watch_out: list[dict[str, str]] = []
    seen_notes: set[str] = set()
    for attempt, evaluation, key, name, title in rows:
        if evaluation.outcome == "correct":
            continue
        activity = db.get(ActivityVersion, attempt.activity_version_id)
        if activity is None or not activity.misconceptions:
            continue
        choice = str(attempt.response.get("choice", ""))
        notes = activity.misconceptions
        note = ""
        if isinstance(notes, dict):
            note = str(notes.get(choice, "")).strip()
        if not note or note in seen_notes:
            continue
        seen_notes.add(note)
        watch_out.append(
            {
                "competency_key": key,
                "competency_name": name,
                "lesson_title": title,
                "note": note,
                "choice": choice,
            }
        )

    return {
        "topics": topics,
        "independent_attempts": independent,
        "unresolved": unresolved,
        "suggested_review": suggested,
        "watch_out_for": watch_out,
        "note": "This summary counts stored attempts only. It does not claim retention.",
    }


def finish_session(
    db: Session,
    user: User,
    session_id: uuid.UUID,
) -> tuple[LearningSession, dict[str, object]]:
    from app.modules.learning.sessions import get_owned_session

    session = get_owned_session(db, user, session_id)
    if session.status != "finished":
        session.status = "finished"
        session.updated_at = datetime.now(timezone.utc)
        already = db.scalar(
            select(SessionEvent).where(
                SessionEvent.session_id == session.id,
                SessionEvent.client_event_id == "server-finish",
            )
        )
        if already is None:
            db.add(
                SessionEvent(
                    session_id=session.id,
                    client_event_id="server-finish",
                    event_type="finish",
                    payload={},
                )
            )
        db.commit()
        db.refresh(session)
    return session, build_summary(db, session)
