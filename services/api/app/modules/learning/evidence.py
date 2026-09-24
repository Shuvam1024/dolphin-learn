"""Turn a graded attempt into competency evidence. Same-session success is not retention."""

import uuid
from datetime import datetime, timezone

from app.errors import ApiError
from app.modules.identity.models import User
from app.modules.learning.models import (
    ActivityVersion,
    Attempt,
    CompetencyEvidence,
    CompetencyState,
    LearningSession,
    Lesson,
    PlanActivity,
    SessionEvent,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

_RANK = {
    "exposed": 1,
    "practicing": 2,
    "independently_demonstrated": 3,
    "retained": 4,
    "applied": 5,
}


def solution_revealed_for_item(
    db: Session,
    user: User,
    activity_id: uuid.UUID,
) -> bool:
    """True when this learner has already seen the solution for this exact item."""
    return (
        db.scalar(
            select(SessionEvent.id)
            .join(LearningSession, SessionEvent.session_id == LearningSession.id)
            .where(
                LearningSession.user_id == user.id,
                SessionEvent.event_type == "solution",
                SessionEvent.payload["activity_version_id"].astext == str(activity_id),
            )
            .limit(1)
        )
        is not None
    )


def facet_for_attempt(
    assistance: str,
    outcome: str,
    *,
    solution_revealed: bool = False,
) -> str:
    """Assisted success is practice. Independent success is a demonstration. Never retention.

    A correct answer on the exact item whose solution was revealed stays practicing.
    """
    if solution_revealed and outcome == "correct":
        facet = "practicing"
    elif assistance == "independent" and outcome == "correct":
        facet = "independently_demonstrated"
    elif outcome == "correct":
        facet = "practicing"
    else:
        facet = "exposed"
    if facet in {"retained", "applied"}:
        raise ApiError(
            "internal_error",
            "Same-session work cannot award retention",
            status_code=500,
        )
    return facet


def record_evidence(
    db: Session,
    user: User,
    session: LearningSession,
    activity: ActivityVersion,
    attempt: Attempt,
    assistance: str,
    outcome: str,
) -> str:
    revealed = solution_revealed_for_item(db, user, activity.id)
    facet = facet_for_attempt(assistance, outcome, solution_revealed=revealed)
    lesson = db.get(Lesson, activity.lesson_id)
    if lesson is None:
        raise ApiError("internal_error", "Activity has no lesson", status_code=500)
    db.add(
        CompetencyEvidence(
            user_id=user.id,
            competency_id=lesson.competency_id,
            attempt_id=attempt.id,
            status_facet=facet,
        )
    )
    if facet == "independently_demonstrated":
        from app.modules.learning.reviews import schedule_independent_success

        schedule_independent_success(db, user.id, lesson.competency_id)
    state = db.get(CompetencyState, (user.id, lesson.competency_id))
    if state is None:
        db.add(
            CompetencyState(
                user_id=user.id,
                competency_id=lesson.competency_id,
                status_facet=facet,
                updated_at=datetime.now(timezone.utc),
            )
        )
        return facet
    if _RANK[facet] > _RANK.get(state.status_facet, 0) and state.status_facet not in {
        "retained",
        "applied",
    }:
        state.status_facet = facet
        state.updated_at = datetime.now(timezone.utc)
    return facet


def record_self_report_evidence(
    db: Session,
    user: User,
    activity: ActivityVersion,
    attempt: Attempt,
    facet: str,
) -> str:
    """Self-report evidence never rises above practicing."""
    if facet not in {"exposed", "practicing"}:
        raise ApiError(
            "internal_error",
            "Self-report evidence cannot exceed practicing",
            status_code=500,
        )
    lesson = db.get(Lesson, activity.lesson_id)
    if lesson is None:
        raise ApiError("internal_error", "Activity has no lesson", status_code=500)
    db.add(
        CompetencyEvidence(
            user_id=user.id,
            competency_id=lesson.competency_id,
            attempt_id=attempt.id,
            status_facet=facet,
        )
    )
    state = db.get(CompetencyState, (user.id, lesson.competency_id))
    now = datetime.now(timezone.utc)
    if state is None:
        db.add(
            CompetencyState(
                user_id=user.id,
                competency_id=lesson.competency_id,
                status_facet=facet,
                updated_at=now,
            )
        )
        return facet
    if state.status_facet in {"retained", "applied", "independently_demonstrated"}:
        return facet
    if _RANK[facet] > _RANK.get(state.status_facet, 0):
        state.status_facet = facet
        state.updated_at = now
    return facet


def award_retained(
    db: Session,
    user: User,
    competency_id: uuid.UUID,
    attempt_id: uuid.UUID,
) -> None:
    """A due independent review can say retained. A same-session attempt cannot call this."""
    db.add(
        CompetencyEvidence(
            user_id=user.id,
            competency_id=competency_id,
            attempt_id=attempt_id,
            status_facet="retained",
        )
    )
    state = db.get(CompetencyState, (user.id, competency_id))
    now = datetime.now(timezone.utc)
    if state is None:
        db.add(
            CompetencyState(
                user_id=user.id,
                competency_id=competency_id,
                status_facet="retained",
                updated_at=now,
            )
        )
        return
    if state.status_facet == "applied":
        return
    if state.status_facet != "retained":
        state.status_facet = "retained"
        state.updated_at = now


def move_to_unseen_question(db: Session, user: User, session_id: uuid.UUID) -> LearningSession:
    """After help, the next check is a different item from the competency pool."""
    from app.modules.learning.sessions import get_owned_session

    session = get_owned_session(db, user, session_id)
    if session.plan_activity_id is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    current = db.get(PlanActivity, session.plan_activity_id)
    if current is None or current.activity_version_id is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    current_activity = db.get(ActivityVersion, current.activity_version_id)
    if current_activity is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    lesson = db.get(Lesson, current_activity.lesson_id)
    if lesson is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    from app.modules.learning.item_pool import pick_next

    picked = pick_next(
        db,
        user,
        lesson.competency_id,
        purpose="fresh_check",
        exclude_ids={current_activity.id},
    )
    if picked is None:
        raise ApiError("validation_error", "No other question is available", status_code=422)
    plan_row = db.scalar(
        select(PlanActivity).where(
            PlanActivity.plan_version_id == current.plan_version_id,
            PlanActivity.activity_version_id == picked.activity.id,
        )
    )
    if plan_row is None:
        raise ApiError("validation_error", "No other question is available", status_code=422)
    session.plan_activity_id = plan_row.id
    session.updated_at = datetime.now(timezone.utc)
    db.add(
        SessionEvent(
            session_id=session.id,
            client_event_id=f"fresh_check:{picked.activity.id}:{uuid.uuid4().hex[:8]}",
            event_type="fresh_check",
            payload={
                "activity_version_id": str(picked.activity.id),
                "repeat": "true" if picked.repeat else "false",
                "selection_reason": picked.selection_reason,
            },
        )
    )
    from app.analytics.events import emit_independent_check_completed

    emit_independent_check_completed(
        db,
        user.id,
        session_id=session.id,
        activity_version_id=picked.activity.id,
    )
    db.commit()
    db.refresh(session)
    return session
