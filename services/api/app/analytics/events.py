"""Privacy-respecting product events and learning-dataset views (S94)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.db import Base
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

EVENT_NAMES = (
    "goal_created",
    "plan_accepted",
    "plan_replanned",
    "session_started",
    "activity_submitted",
    "hint_requested",
    "explain_requested",
    "independent_check_completed",
    "review_completed",
    "review_snoozed",
    "account_export_requested",
    "account_deletion_requested",
)

# Keys that must never appear in product_events.props (raw learner content / PII).
FORBIDDEN_PROP_KEYS = frozenset(
    {
        "email",
        "raw_request",
        "title",
        "prompt",
        "answer",
        "response",
        "text",
        "choice",
        "note",
        "notes",
        "explanation",
        "hint",
        "body",
        "markdown",
        "name",
        "display_name",
    }
)


class ProductEvent(Base):
    __tablename__ = "product_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    props: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


def _opaque(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _sanitize_props(props: dict[str, Any] | None) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in (props or {}).items():
        lowered = str(key).casefold()
        if lowered in FORBIDDEN_PROP_KEYS or any(
            token in lowered for token in ("email", "answer", "prompt", "raw_")
        ):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            # Reject long free text even under opaque-looking keys.
            if isinstance(value, str) and len(value) > 64:
                continue
            if isinstance(value, str) and "@" in value:
                continue
            clean[str(key)] = value
        elif isinstance(value, uuid.UUID):
            clean[str(key)] = str(value)
    return clean


def emit(
    db: Session,
    user_id: uuid.UUID,
    name: str,
    props: dict[str, Any] | None = None,
    *,
    flush: bool = True,
) -> ProductEvent:
    """Append a product event. Props must be opaque ids / enums / counts only."""
    if name not in EVENT_NAMES:
        raise ValueError(f"unknown product event: {name}")
    row = ProductEvent(
        user_id=user_id,
        name=name,
        props=_sanitize_props(props),
    )
    db.add(row)
    if flush:
        db.flush()
    return row


def emit_goal_created(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID, *, domain_key: str) -> None:
    emit(db, user_id, "goal_created", {"goal_id": _opaque(goal_id), "domain_key": domain_key})


def emit_plan_accepted(
    db: Session, user_id: uuid.UUID, goal_id: uuid.UUID, *, plan_version_id: uuid.UUID, version_number: int
) -> None:
    emit(
        db,
        user_id,
        "plan_accepted",
        {
            "goal_id": _opaque(goal_id),
            "plan_version_id": _opaque(plan_version_id),
            "version_number": int(version_number),
        },
    )


def emit_plan_replanned(
    db: Session, user_id: uuid.UUID, goal_id: uuid.UUID, *, plan_version_id: uuid.UUID, version_number: int
) -> None:
    emit(
        db,
        user_id,
        "plan_replanned",
        {
            "goal_id": _opaque(goal_id),
            "plan_version_id": _opaque(plan_version_id),
            "version_number": int(version_number),
        },
    )


def emit_session_started(
    db: Session, user_id: uuid.UUID, session_id: uuid.UUID, *, goal_id: uuid.UUID | None = None
) -> None:
    props: dict[str, Any] = {"session_id": _opaque(session_id)}
    if goal_id is not None:
        props["goal_id"] = _opaque(goal_id)
    emit(db, user_id, "session_started", props)


def emit_activity_submitted(
    db: Session,
    user_id: uuid.UUID,
    *,
    attempt_id: uuid.UUID,
    activity_version_id: uuid.UUID,
    session_id: uuid.UUID | None = None,
) -> None:
    props: dict[str, Any] = {
        "attempt_id": _opaque(attempt_id),
        "activity_version_id": _opaque(activity_version_id),
    }
    if session_id is not None:
        props["session_id"] = _opaque(session_id)
    emit(db, user_id, "activity_submitted", props)


def emit_hint_requested(db: Session, user_id: uuid.UUID, *, session_id: uuid.UUID, activity_version_id: uuid.UUID) -> None:
    emit(
        db,
        user_id,
        "hint_requested",
        {
            "session_id": _opaque(session_id),
            "activity_version_id": _opaque(activity_version_id),
        },
    )


def emit_explain_requested(
    db: Session, user_id: uuid.UUID, *, session_id: uuid.UUID, activity_version_id: uuid.UUID
) -> None:
    emit(
        db,
        user_id,
        "explain_requested",
        {
            "session_id": _opaque(session_id),
            "activity_version_id": _opaque(activity_version_id),
        },
    )


def emit_independent_check_completed(
    db: Session, user_id: uuid.UUID, *, session_id: uuid.UUID, activity_version_id: uuid.UUID | None = None
) -> None:
    props: dict[str, Any] = {"session_id": _opaque(session_id)}
    if activity_version_id is not None:
        props["activity_version_id"] = _opaque(activity_version_id)
    emit(db, user_id, "independent_check_completed", props)


def emit_review_completed(
    db: Session, user_id: uuid.UUID, *, review_item_id: uuid.UUID, outcome: str
) -> None:
    emit(
        db,
        user_id,
        "review_completed",
        {"review_item_id": _opaque(review_item_id), "outcome": outcome},
    )


def emit_review_snoozed(
    db: Session, user_id: uuid.UUID, *, review_item_id: uuid.UUID, hours: int
) -> None:
    emit(
        db,
        user_id,
        "review_snoozed",
        {"review_item_id": _opaque(review_item_id), "hours": int(hours)},
    )


def emit_account_export_requested(db: Session, user_id: uuid.UUID) -> None:
    emit(db, user_id, "account_export_requested", {})


def emit_account_deletion_requested(db: Session, user_id: uuid.UUID) -> None:
    emit(db, user_id, "account_deletion_requested", {})
