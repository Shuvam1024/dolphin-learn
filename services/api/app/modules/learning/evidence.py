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
)
from sqlalchemy import select
from sqlalchemy.orm import Session

_RANK = {"exposed": 1, "practicing": 2, "independently_demonstrated": 3}


def facet_for_attempt(assistance: str, outcome: str) -> str:
    """Assisted success is practice. Independent success is a demonstration. Never retention."""
    if assistance == "independent" and outcome == "correct":
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
    facet = facet_for_attempt(assistance, outcome)
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


def move_to_unseen_question(db: Session, user: User, session_id: uuid.UUID) -> LearningSession:
    """After help, the next check is a different seeded question."""
    from app.modules.learning.sessions import get_owned_session

    session = get_owned_session(db, user, session_id)
    if session.plan_activity_id is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    current = db.get(PlanActivity, session.plan_activity_id)
    if current is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    rows = db.execute(
        select(PlanActivity, ActivityVersion)
        .join(ActivityVersion, PlanActivity.activity_version_id == ActivityVersion.id)
        .where(
            PlanActivity.plan_version_id == current.plan_version_id,
            ActivityVersion.activity_type == "objective",
            PlanActivity.id != current.id,
        )
        .order_by(PlanActivity.position)
    ).all()
    if not rows:
        raise ApiError("validation_error", "No other question is available", status_code=422)
    session.plan_activity_id = rows[0][0].id
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session
