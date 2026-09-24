"""Pick graded practice items the learner has not seen yet."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.modules.identity.models import User
from app.modules.learning.models import ActivityVersion, Attempt, Lesson
from sqlalchemy import func, select
from sqlalchemy.orm import Session

GRADED_TYPES = ("objective", "short_answer", "numeric")


@dataclass(frozen=True)
class PickResult:
    activity: ActivityVersion
    repeat: bool


def pick_unseen(
    db: Session,
    user: User,
    competency_id: uuid.UUID,
    exclude_ids: set[uuid.UUID] | list[uuid.UUID] | None = None,
    *,
    graded: bool = True,
) -> PickResult | None:
    """Never-attempted first, then least-recently attempted.

    When ``graded=True``, provisional items are excluded so AI drafts never grade.
    ``repeat`` is true when every eligible item has already been attempted.
    """
    excluded = {uuid.UUID(str(item)) for item in (exclude_ids or [])}
    query = (
        select(ActivityVersion)
        .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
        .where(
            Lesson.competency_id == competency_id,
            ActivityVersion.activity_type.in_(GRADED_TYPES),
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
        return PickResult(activity=never[0], repeat=False)

    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    candidates.sort(key=lambda item: (last_seen[item.id] or epoch, item.version, item.id))
    return PickResult(activity=candidates[0], repeat=True)
