"""Pick graded practice items the learner has not seen yet."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from app.modules.identity.models import User
from app.modules.learning.models import ActivityVersion, Attempt, Evaluation, Lesson, SessionEvent
from sqlalchemy import func, select
from sqlalchemy.orm import Session

GRADED_TYPES = ("objective", "short_answer", "numeric")

Purpose = Literal["first", "fresh_check", "review", "retry"]


@dataclass(frozen=True)
class PickResult:
    activity: ActivityVersion
    repeat: bool
    selection_reason: str = "unseen"


def pick_unseen(
    db: Session,
    user: User,
    competency_id: uuid.UUID,
    exclude_ids: set[uuid.UUID] | list[uuid.UUID] | None = None,
    *,
    graded: bool = True,
    activity_types: tuple[str, ...] | list[str] | None = None,
) -> PickResult | None:
    """Never-attempted first, then least-recently attempted.

    When ``graded=True``, provisional items are excluded so AI drafts never grade.
    ``repeat`` is true when every eligible item has already been attempted.
    """
    excluded = {uuid.UUID(str(item)) for item in (exclude_ids or [])}
    types = tuple(activity_types) if activity_types else GRADED_TYPES
    query = (
        select(ActivityVersion)
        .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
        .where(
            Lesson.competency_id == competency_id,
            ActivityVersion.activity_type.in_(types),
        )
    )
    if excluded:
        query = query.where(ActivityVersion.id.notin_(excluded))
    if graded:
        query = query.where(ActivityVersion.provisional.is_(False))
    candidates = list(db.scalars(query.order_by(ActivityVersion.version, ActivityVersion.id)))
    if not candidates:
        return None

    last_seen: dict[uuid.UUID, datetime | None] = {}
    for activity in candidates:
        latest = db.scalar(
            select(func.max(Attempt.submitted_at)).where(
                Attempt.user_id == user.id,
                Attempt.activity_version_id == activity.id,
            )
        )
        last_seen[activity.id] = latest

    never = [item for item in candidates if last_seen[item.id] is None]
    if never:
        return PickResult(activity=never[0], repeat=False, selection_reason="unseen")

    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    candidates.sort(key=lambda item: (last_seen[item.id] or epoch, item.version, item.id))
    return PickResult(activity=candidates[0], repeat=True, selection_reason="least_recent")


def _difficulty(activity: ActivityVersion) -> int:
    value = activity.difficulty
    if value is None:
        return 2
    return int(value)


def _last_assist_and_outcome(
    db: Session, user: User, competency_id: uuid.UUID
) -> tuple[str | None, str | None, int | None]:
    """Return (assistance, outcome, difficulty) for the most recent graded attempt."""
    row = db.execute(
        select(Evaluation.assistance, Evaluation.outcome, ActivityVersion.difficulty)
        .join(Attempt, Evaluation.attempt_id == Attempt.id)
        .join(ActivityVersion, Attempt.activity_version_id == ActivityVersion.id)
        .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
        .where(Attempt.user_id == user.id, Lesson.competency_id == competency_id)
        .order_by(Attempt.submitted_at.desc(), Attempt.id.desc())
        .limit(1)
    ).first()
    if row is None:
        return None, None, None
    return str(row[0]), str(row[1]), (int(row[2]) if row[2] is not None else 2)


def _revealed_ids(db: Session, user: User) -> set[uuid.UUID]:
    from app.modules.learning.models import LearningSession

    rows = db.execute(
        select(SessionEvent.payload)
        .join(LearningSession, SessionEvent.session_id == LearningSession.id)
        .where(
            LearningSession.user_id == user.id,
            SessionEvent.event_type == "solution",
        )
    ).all()
    revealed: set[uuid.UUID] = set()
    for (payload,) in rows:
        raw = str((payload or {}).get("activity_version_id") or "")
        try:
            revealed.add(uuid.UUID(raw))
        except ValueError:
            continue
    return revealed


def pick_next(
    db: Session,
    user: User,
    competency_id: uuid.UUID,
    purpose: Purpose = "first",
    *,
    exclude_ids: set[uuid.UUID] | list[uuid.UUID] | None = None,
) -> PickResult | None:
    """Select by difficulty, recency, and assistance history. Never provisional for grading."""
    excluded = {uuid.UUID(str(item)) for item in (exclude_ids or [])}
    excluded |= _revealed_ids(db, user)

    candidates = list(
        db.scalars(
            select(ActivityVersion)
            .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
            .where(
                Lesson.competency_id == competency_id,
                ActivityVersion.activity_type.in_(GRADED_TYPES),
                ActivityVersion.provisional.is_(False),
            )
            .order_by(ActivityVersion.version, ActivityVersion.id)
        )
    )
    candidates = [item for item in candidates if item.id not in excluded]
    if not candidates:
        return None

    assistance, outcome, last_diff = _last_assist_and_outcome(db, user, competency_id)
    target_levels: set[int]
    reason: str

    if purpose == "first" or (assistance is None and outcome is None):
        target_levels = {1, 2}
        reason = "first_easy"
    elif purpose == "fresh_check" and assistance == "none" and outcome == "correct":
        nxt = min(3, (last_diff or 1) + 1)
        target_levels = {nxt}
        reason = "step_up_after_independent"
    elif purpose in {"fresh_check", "retry"} or (
        assistance in {"hint", "solution", "guided"} or outcome in {"incorrect", "wrong"}
    ):
        level = last_diff or 2
        target_levels = {level, max(1, level - 1)}
        reason = "same_or_lower_after_assisted_or_incorrect"
    elif purpose == "review":
        target_levels = {1, 2, 3}
        reason = "review_alternate"
    else:
        target_levels = {1, 2, 3}
        reason = "fallback_pool"

    preferred = [item for item in candidates if _difficulty(item) in target_levels]
    pool = preferred or candidates

    if purpose == "review" and last_diff is not None:
        opposite = [item for item in pool if _difficulty(item) != last_diff]
        if opposite:
            pool = opposite
            reason = "review_alternate_difficulty"

    last_seen: dict[uuid.UUID, datetime | None] = {}
    for activity in pool:
        latest = db.scalar(
            select(func.max(Attempt.submitted_at)).where(
                Attempt.user_id == user.id,
                Attempt.activity_version_id == activity.id,
            )
        )
        last_seen[activity.id] = latest

    never = [item for item in pool if last_seen[item.id] is None]
    if never:
        never.sort(key=lambda item: (_difficulty(item), item.version, item.id))
        return PickResult(activity=never[0], repeat=False, selection_reason=reason)

    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    pool.sort(
        key=lambda item: (
            last_seen[item.id] or epoch,
            _difficulty(item),
            item.version,
            item.id,
        )
    )
    return PickResult(activity=pool[0], repeat=True, selection_reason=f"{reason}|least_recent")
