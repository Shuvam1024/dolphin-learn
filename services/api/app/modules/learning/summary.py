"""Honest end-of-session summary built from stored attempts."""

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
    ReviewItem,
    SessionEvent,
)
from app.modules.learning.study_time import session_active_minutes
from sqlalchemy import select
from sqlalchemy.orm import Session


def _plan_version_id(db: Session, session: LearningSession):
    if session.plan_activity_id is None:
        return None
    plan = db.get(PlanActivity, session.plan_activity_id)
    if plan is None:
        return None
    return plan.plan_version_id


def _goal_id(db: Session, session: LearningSession) -> str:
    from app.modules.learning.models import LearningPath, PlanVersion

    version_id = _plan_version_id(db, session)
    if version_id is None:
        return ""
    version = db.get(PlanVersion, version_id)
    if version is None:
        return ""
    path = db.get(LearningPath, version.learning_path_id)
    return str(path.goal_id) if path is not None else ""


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

    showed: list[dict[str, str]] = []
    practiced: list[dict[str, str]] = []
    self_reported: list[dict[str, str]] = []
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
        item = {
            "attempt_id": str(attempt.id),
            "competency_key": key,
            "competency_name": name,
            "lesson_title": title,
            "outcome": evaluation.outcome,
            "choice": str(
                attempt.response.get("choice")
                or attempt.response.get("text")
                or attempt.response.get("value")
                or ""
            ),
        }
        if evaluation.evaluator == "self_report" and evaluation.outcome == "self_reported":
            self_reported.append({**item, "rating": str(attempt.response.get("self_rating", ""))})
        elif evaluation.assistance == "independent" and evaluation.outcome == "correct":
            showed.append(item)
            independent.append(item)
            demonstrated.add(key)
        elif evaluation.assistance == "assisted":
            practiced.append(item)
        elif evaluation.assistance == "independent":
            independent.append(item)

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
        note = ""
        source = "seed"
        if evaluation.feedback_json:
            note = str(evaluation.feedback_json.get("misconception_note", "") or "").strip()
            source = str(evaluation.feedback_json.get("misconception_source", "ai") or "ai")
        if not note:
            activity = db.get(ActivityVersion, attempt.activity_version_id)
            if activity is None or not activity.misconceptions:
                continue
            choice = str(attempt.response.get("choice", ""))
            notes = activity.misconceptions
            if isinstance(notes, dict):
                note = str(notes.get(choice, "")).strip()
            source = "seed"
        if not note or note in seen_notes:
            continue
        seen_notes.add(note)
        watch_out.append(
            {
                "competency_key": key,
                "competency_name": name,
                "lesson_title": title,
                "note": note,
                "choice": str(attempt.response.get("choice", "")),
                "source": source,
            }
        )

    next_review: dict[str, object] | None = None
    review = db.scalar(
        select(ReviewItem)
        .where(ReviewItem.user_id == session.user_id)
        .order_by(ReviewItem.due_at)
    )
    if review is not None:
        competency = db.get(Competency, review.competency_id)
        days = max(
            0,
            int((review.due_at - datetime.now(timezone.utc)).total_seconds() // 86400),
        )
        next_review = {
            "lesson": competency.name if competency is not None else "",
            "in_days": days,
        }

    goal_id = _goal_id(db, session)
    next_step = {
        "kind": "home",
        "href": "/app",
        "label": "Back to Home",
    }
    if goal_id:
        next_step = {
            "kind": "goal",
            "href": f"/app/goals/{goal_id}",
            "label": "Back to your path",
        }

    return {
        "topics": topics,
        "independent_attempts": independent,
        "unresolved": unresolved,
        "suggested_review": suggested,
        "watch_out_for": watch_out,
        "showed_on_your_own": showed,
        "practiced_with_help": practiced,
        "self_reported": self_reported,
        "next_review": next_review,
        "minutes_studied": session_active_minutes(db, session),
        "next_step": next_step,
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
