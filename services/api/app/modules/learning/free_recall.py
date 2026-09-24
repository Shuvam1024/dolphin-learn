"""Free-recall self-report with a hard evidence ceiling."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.errors import ApiError
from app.modules.ai_gateway.schemas import GatewayError
from app.modules.ai_gateway.service import complete, is_enabled
from app.modules.identity.models import User
from app.modules.learning.evidence import record_self_report_evidence
from app.modules.learning.models import (
    ActivityVersion,
    Attempt,
    Evaluation,
    LearningSession,
    Lesson,
    PlanActivity,
)
from app.modules.learning.sessions import get_owned_session
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

_RATINGS = frozenset({"got_it", "partly", "not_yet"})


class RecallCompareOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    covered: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    one_sentence_feedback: str = Field(max_length=200)


def facet_for_self_rating(rating: str) -> str:
    if rating in {"got_it", "partly"}:
        return "practicing"
    return "exposed"


def _current_free_recall(db: Session, session: LearningSession) -> ActivityVersion:
    if session.plan_activity_id is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    plan = db.get(PlanActivity, session.plan_activity_id)
    if plan is None or plan.activity_version_id is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    activity = db.get(ActivityVersion, plan.activity_version_id)
    if activity is None or activity.activity_type != "free_recall":
        raise ApiError("validation_error", "This activity is not free recall", status_code=422)
    return activity


def maybe_recall_compare(
    db: Session,
    user: User,
    activity: ActivityVersion,
    *,
    learner_text: str,
) -> dict[str, object] | None:
    if not is_enabled(db, user):
        return None
    lesson = db.get(Lesson, activity.lesson_id)
    reading = lesson.body_markdown if lesson is not None else ""
    try:
        result = complete(
            db,
            user,
            "recall_compare",
            {"lesson": reading, "learner_text": learner_text},
            RecallCompareOut,
            timeout=12.0,
        )
        assert isinstance(result, RecallCompareOut)
    except GatewayError:
        return None
    return {
        "covered": list(result.covered)[:12],
        "missing": list(result.missing)[:12],
        "one_sentence_feedback": result.one_sentence_feedback.strip()[:200],
        "source": "ai",
    }


def submit_free_recall_text(
    db: Session,
    user: User,
    session_id: uuid.UUID,
    *,
    idempotency_key: str,
    text: str,
) -> tuple[Attempt, bool]:
    session = get_owned_session(db, user, session_id)
    existing = db.scalar(
        select(Attempt).where(
            Attempt.session_id == session.id,
            Attempt.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing, False
    if not text.strip():
        raise ApiError("validation_error", "text is required", status_code=422)
    activity = _current_free_recall(db, session)
    prior = db.scalar(
        select(Attempt)
        .where(
            Attempt.session_id == session.id,
            Attempt.activity_version_id == activity.id,
        )
        .order_by(Attempt.submitted_at.desc())
    )
    if prior is not None:
        evaluation = db.scalar(select(Evaluation).where(Evaluation.attempt_id == prior.id))
        if evaluation is None or evaluation.outcome == "awaiting_self_report":
            return prior, False
    compare = maybe_recall_compare(db, user, activity, learner_text=text)
    attempt = Attempt(
        user_id=user.id,
        activity_version_id=activity.id,
        session_id=session.id,
        idempotency_key=idempotency_key,
        response={
            "text": text,
            "prompt": activity.prompt,
            "assistance": "independent",
            "phase": "awaiting_self_report",
        },
    )
    db.add(attempt)
    db.flush()
    db.add(
        Evaluation(
            attempt_id=attempt.id,
            score=None,
            assistance="independent",
            outcome="awaiting_self_report",
            evaluator="self_report",
            feedback_json=compare,
        )
    )
    db.commit()
    db.refresh(attempt)
    return attempt, True


def submit_self_rating(
    db: Session,
    user: User,
    session_id: uuid.UUID,
    *,
    rating: str,
) -> dict[str, Any]:
    if rating not in _RATINGS:
        raise ApiError(
            "validation_error",
            "rating must be got_it, partly, or not_yet",
            status_code=422,
        )
    session = get_owned_session(db, user, session_id)
    activity = _current_free_recall(db, session)
    attempt = db.scalar(
        select(Attempt)
        .where(
            Attempt.session_id == session.id,
            Attempt.activity_version_id == activity.id,
        )
        .order_by(Attempt.submitted_at.desc())
    )
    if attempt is None:
        raise ApiError("validation_error", "Write from memory before rating", status_code=422)
    evaluation = db.scalar(select(Evaluation).where(Evaluation.attempt_id == attempt.id))
    if evaluation is None:
        raise ApiError("validation_error", "Write from memory before rating", status_code=422)
    if evaluation.outcome == "self_reported":
        return {
            "rating": str(attempt.response.get("self_rating", rating)),
            "outcome": "self_reported",
            "facet": facet_for_self_rating(str(attempt.response.get("self_rating", rating))),
        }
    if evaluation.outcome != "awaiting_self_report":
        raise ApiError(
            "validation_error",
            "This attempt is not awaiting a self-rating",
            status_code=422,
        )
    facet = facet_for_self_rating(rating)
    attempt.response = {
        **attempt.response,
        "self_rating": rating,
        "phase": "rated",
    }
    flag_modified(attempt, "response")
    evaluation.outcome = "self_reported"
    if rating == "got_it":
        evaluation.score = Decimal("1.00")
    elif rating == "partly":
        evaluation.score = Decimal("0.50")
    else:
        evaluation.score = Decimal("0.00")
    feedback = dict(evaluation.feedback_json or {})
    feedback["self_rating"] = rating
    evaluation.feedback_json = feedback
    record_self_report_evidence(db, user, activity, attempt, facet)
    if rating == "got_it":
        from app.modules.learning.reviews import schedule_independent_success

        lesson = db.get(Lesson, activity.lesson_id)
        if lesson is not None:
            schedule_independent_success(db, user.id, lesson.competency_id)
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"rating": rating, "outcome": "self_reported", "facet": facet}
