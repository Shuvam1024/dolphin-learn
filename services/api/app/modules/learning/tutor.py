"""Tutor: explain differently and validated hints. The referee stays deterministic."""

from __future__ import annotations

import re
import uuid
from typing import Any

from app.errors import ApiError
from app.modules.ai_gateway.schemas import GatewayError
from app.modules.ai_gateway.service import complete, is_enabled
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
from app.modules.learning.sessions import _current_objective, get_owned_session
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

SEEDED_HINT = "Compare each choice with the note. The letter stays hidden."
_ANSWER_PHRASE = re.compile(r"\bthe answer is\b", re.I)


class HintOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hint: str = Field(max_length=280)


class ExplainOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    explanation_markdown: str = Field(max_length=900)
    analogy_used: bool = False


def hint_validator(activity: ActivityVersion, hint: str) -> bool:
    """Reject hints that leak the key, an alternate, or 'the answer is'."""
    text = hint.strip()
    if not text or _ANSWER_PHRASE.search(text):
        return False
    folded = text.casefold()
    key = activity.answer_key or {}
    correct = str(key.get("correct", "")).strip()
    if correct and re.search(rf"\b{re.escape(correct)}\b", folded, re.I):
        return False
    payload = activity.payload or {}
    alternates = payload.get("alternates") if isinstance(payload, dict) else None
    if isinstance(alternates, list):
        for alt in alternates:
            if str(alt).strip() and str(alt).casefold() in folded:
                return False
    if activity.activity_type == "numeric":
        try:
            expected = float(str(key.get("correct", "")))
        except ValueError:
            expected = None
        if expected is not None:
            tolerance = 0.0
            if isinstance(payload, dict) and payload.get("tolerance") is not None:
                try:
                    tolerance = float(payload["tolerance"])
                except (TypeError, ValueError):
                    tolerance = 0.0
            for match in re.findall(r"-?\d+(?:\.\d+)?", text):
                try:
                    value = float(match)
                except ValueError:
                    continue
                if abs(value - expected) <= tolerance + 1e-9:
                    return False
    if activity.activity_type == "objective" and isinstance(payload, dict):
        choices = payload.get("choices")
        if isinstance(choices, list) and correct:
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                if str(choice.get("id", "")).strip().lower() != correct.lower():
                    continue
                label = str(choice.get("label", "")).strip()
                if label and label.casefold() in folded:
                    return False
    return True


def help_event_count(db: Session, session_id: uuid.UUID, activity_id: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(SessionEvent)
            .where(
                SessionEvent.session_id == session_id,
                SessionEvent.event_type.in_(("hint", "explain_requested", "solution")),
                SessionEvent.payload["activity_version_id"].astext == str(activity_id),
            )
        )
        or 0
    )


def _latest_help_payload(
    db: Session,
    session: LearningSession,
    activity_id: uuid.UUID,
    event_type: str,
) -> dict[str, str]:
    event = db.scalar(
        select(SessionEvent)
        .where(
            SessionEvent.session_id == session.id,
            SessionEvent.event_type == event_type,
            SessionEvent.payload["activity_version_id"].astext == str(activity_id),
        )
        .order_by(SessionEvent.created_at.desc(), SessionEvent.id.desc())
    )
    if event is None:
        return {}
    return {str(key): str(value) for key, value in event.payload.items()}


def tutor_state(db: Session, session: LearningSession, activity_id: uuid.UUID) -> dict[str, str]:
    hint = _latest_help_payload(db, session, activity_id, "hint")
    explain = _latest_help_payload(db, session, activity_id, "explain_requested")
    return {
        "hint_text": hint.get("message", ""),
        "hint_source": hint.get("source", "seed") if hint.get("message") else "seed",
        "alt_explanation": explain.get("explanation_markdown", ""),
    }


def _reading_for(db: Session, activity: ActivityVersion) -> str:
    lesson = db.get(Lesson, activity.lesson_id)
    return lesson.body_markdown if lesson is not None else ""


def _last_wrong(db: Session, user: User, session: LearningSession, activity_id: uuid.UUID) -> str:
    latest = db.scalar(
        select(Attempt)
        .where(
            Attempt.user_id == user.id,
            Attempt.session_id == session.id,
            Attempt.activity_version_id == activity_id,
        )
        .order_by(Attempt.submitted_at.desc())
    )
    if latest is None:
        return ""
    evaluation = db.scalar(select(Evaluation).where(Evaluation.attempt_id == latest.id))
    if evaluation is None or evaluation.outcome == "correct":
        return ""
    return str(latest.response.get("choice", "") or latest.response.get("text", ""))


def _store_event(
    db: Session,
    session: LearningSession,
    *,
    event_type: str,
    client_event_id: str,
    payload: dict[str, str],
) -> None:
    existing = db.scalar(
        select(SessionEvent).where(
            SessionEvent.session_id == session.id,
            SessionEvent.client_event_id == client_event_id,
        )
    )
    if existing is not None:
        return
    db.add(
        SessionEvent(
            session_id=session.id,
            client_event_id=client_event_id,
            event_type=event_type,
            payload=payload,
        )
    )


def request_hint(
    db: Session,
    user: User,
    session_id: uuid.UUID,
    *,
    mode: str,
) -> dict[str, str]:
    if mode == "challenge":
        raise ApiError(
            "forbidden",
            "Hints and solutions stay hidden in challenge mode",
            status_code=403,
        )
    session = get_owned_session(db, user, session_id)
    activity = _current_objective(db, session)
    source = "seed"
    message = SEEDED_HINT
    if is_enabled(db, user):
        try:
            variables: dict[str, Any] = {
                "prompt": activity.prompt,
                "reading": _reading_for(db, activity),
                "last_wrong_response": _last_wrong(db, user, session, activity.id),
            }
            result = complete(db, user, "hint", variables, HintOut, timeout=12.0)
            assert isinstance(result, HintOut)
            if hint_validator(activity, result.hint):
                message = result.hint.strip()
                source = "ai"
        except GatewayError:
            message = SEEDED_HINT
            source = "seed"
    event_id = f"hint:{activity.id}:{uuid.uuid4().hex[:8]}"
    _store_event(
        db,
        session,
        event_type="hint",
        client_event_id=event_id,
        payload={
            "activity_version_id": str(activity.id),
            "message": message,
            "source": source,
        },
    )
    from app.analytics.events import emit_hint_requested

    emit_hint_requested(db, user.id, session_id=session.id, activity_version_id=activity.id)
    db.commit()
    return {
        "kind": "hint",
        "message": message,
        "revealed_choice": "",
        "hint_source": source,
    }


def request_explain(
    db: Session,
    user: User,
    session_id: uuid.UUID,
) -> dict[str, Any]:
    if not is_enabled(db, user):
        raise ApiError("not_found", "Explain is not available", status_code=404)
    session = get_owned_session(db, user, session_id)
    if session.plan_activity_id is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    plan = db.get(PlanActivity, session.plan_activity_id)
    if plan is None or plan.activity_version_id is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    activity = db.get(ActivityVersion, plan.activity_version_id)
    if activity is None:
        raise ApiError("validation_error", "Session has no activity", status_code=422)
    explanation = ""
    analogy_used = False
    try:
        variables = {
            "reading": _reading_for(db, activity),
            "item_prompt": activity.prompt,
            "last_wrong_response": _last_wrong(db, user, session, activity.id),
            "learner_words": "",
        }
        result = complete(db, user, "explain_differently", variables, ExplainOut, timeout=12.0)
        assert isinstance(result, ExplainOut)
        explanation = result.explanation_markdown.strip()
        analogy_used = result.analogy_used
    except GatewayError as exc:
        raise ApiError(
            "unavailable",
            "Explain is temporarily unavailable",
            status_code=503,
        ) from exc
    if not explanation:
        raise ApiError(
            "unavailable",
            "Explain is temporarily unavailable",
            status_code=503,
        )
    event_id = f"explain:{activity.id}:{uuid.uuid4().hex[:8]}"
    _store_event(
        db,
        session,
        event_type="explain_requested",
        client_event_id=event_id,
        payload={
            "activity_version_id": str(activity.id),
            "explanation_markdown": explanation[:900],
            "analogy_used": "true" if analogy_used else "false",
        },
    )
    from app.analytics.events import emit_explain_requested

    emit_explain_requested(db, user.id, session_id=session.id, activity_version_id=activity.id)
    db.commit()
    return {
        "explanation_markdown": explanation,
        "analogy_used": analogy_used,
        "hint_count": help_event_count(db, session.id, activity.id),
    }
