"""Due reviews from independent success. Intervals are plain day counts, not a branded scheduler."""

import uuid
from datetime import datetime, timedelta, timezone

from app.errors import ApiError
from app.modules.curriculum.models import Competency
from app.modules.identity.models import User
from app.modules.learning.evidence import award_retained
from app.modules.learning.grading import grade_choice
from app.modules.learning.item_pool import pick_unseen
from app.modules.learning.models import (
    ActivityVersion,
    Attempt,
    Evaluation,
    Lesson,
    ReviewEvent,
    ReviewItem,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

_STAGES = (1, 3, 7, 14)
_GRADED = {
    "independent_correct",
    "assisted_correct",
    "independent_incorrect",
    "assisted_incorrect",
}


def schedule_independent_success(
    db: Session,
    user_id: uuid.UUID,
    competency_id: uuid.UUID,
) -> ReviewItem:
    """First independent success schedules a future check. A later success does not extend it."""
    existing = db.scalar(
        select(ReviewItem).where(
            ReviewItem.user_id == user_id,
            ReviewItem.competency_id == competency_id,
        )
    )
    if existing is not None:
        return existing
    item = ReviewItem(
        user_id=user_id,
        competency_id=competency_id,
        due_at=datetime.now(timezone.utc) + timedelta(days=_STAGES[0]),
        interval_days=_STAGES[0],
    )
    db.add(item)
    db.flush()
    return item


def _reason(interval_days: int, due_now: bool) -> str:
    if due_now:
        return (
            f"Due after a {interval_days}-day interval from an independent check. Not retention."
        )
    return (
        f"Scheduled {interval_days} day(s) after an independent success. "
        "Not due yet. Not retention."
    )


def _objective(db: Session, user: User, competency_id: uuid.UUID) -> ActivityVersion:
    picked = pick_unseen(db, user, competency_id, graded=True)
    if picked is None:
        raise ApiError("validation_error", "No review question is seeded", status_code=422)
    return picked.activity


def _payload(db: Session, user: User, item: ReviewItem, *, due_now: bool) -> dict[str, object]:
    competency = db.get(Competency, item.competency_id)
    activity = _objective(db, user, item.competency_id)
    lesson = db.get(Lesson, activity.lesson_id)
    revealed = ""
    if _solution_pending(db, item.id) and activity.answer_key is not None:
        revealed = str(activity.answer_key.get("correct", ""))
    return {
        "id": str(item.id),
        "competency_key": competency.key if competency is not None else "",
        "competency_name": competency.name if competency is not None else "",
        "lesson_title": lesson.title if lesson is not None else "",
        "due_at": item.due_at.isoformat(),
        "interval_days": item.interval_days,
        "reason": _reason(item.interval_days, due_now),
        "title": lesson.title if lesson is not None else "",
        "prompt": activity.prompt,
        "revealed_choice": revealed,
    }


def queue_for_user(db: Session, user: User) -> dict[str, list[dict[str, object]]]:
    now = datetime.now(timezone.utc)
    rows = db.scalars(
        select(ReviewItem).where(ReviewItem.user_id == user.id).order_by(ReviewItem.due_at)
    ).all()
    due: list[dict[str, object]] = []
    scheduled: list[dict[str, object]] = []
    for item in rows:
        due_now = item.due_at <= now
        payload = _payload(db, user, item, due_now=due_now)
        if due_now:
            due.append(payload)
        else:
            scheduled.append(payload)
    return {"due": due, "scheduled": scheduled}


def get_owned_review(db: Session, user: User, review_id: uuid.UUID) -> ReviewItem:
    item = db.get(ReviewItem, review_id)
    if item is None or item.user_id != user.id:
        raise ApiError("not_found", "Review not found", status_code=404)
    return item


def _solution_pending(db: Session, review_id: uuid.UUID) -> bool:
    events = db.scalars(
        select(ReviewEvent)
        .where(ReviewEvent.review_item_id == review_id)
        .order_by(ReviewEvent.created_at, ReviewEvent.id)
    ).all()
    pending = False
    for event in events:
        if event.outcome == "solution":
            pending = True
        elif event.outcome in _GRADED:
            pending = False
    return pending


def reveal_solution(db: Session, user: User, review_id: uuid.UUID, *, mode: str) -> dict[str, str]:
    if mode == "challenge":
        raise ApiError(
            "forbidden",
            "Hints and solutions stay hidden in challenge mode",
            status_code=403,
        )
    item = get_owned_review(db, user, review_id)
    activity = _objective(db, user, item.competency_id)
    correct = ""
    if activity.answer_key is not None:
        correct = str(activity.answer_key.get("correct", ""))
    if not _solution_pending(db, item.id):
        db.add(ReviewEvent(review_item_id=item.id, outcome="solution"))
        db.commit()
    return {"revealed_choice": correct}


def _next_interval(current: int) -> int:
    for stage in _STAGES:
        if stage > current:
            return stage
    return _STAGES[-1]


def submit_review_attempt(
    db: Session,
    user: User,
    review_id: uuid.UUID,
    *,
    choice: str,
) -> dict[str, object]:
    item = get_owned_review(db, user, review_id)
    activity = _objective(db, user, item.competency_id)
    assisted = _solution_pending(db, item.id)
    assistance = "assisted" if assisted else "independent"
    outcome, score = grade_choice(activity.answer_key, choice)
    attempt = Attempt(
        user_id=user.id,
        activity_version_id=activity.id,
        session_id=None,
        response={"choice": choice, "prompt": activity.prompt, "assistance": assistance},
    )
    db.add(attempt)
    db.flush()
    db.add(
        Evaluation(
            attempt_id=attempt.id,
            score=score,
            assistance=assistance,
            outcome=outcome,
            evaluator="deterministic",
        )
    )
    label = f"{assistance}_{outcome}"
    db.add(ReviewEvent(review_item_id=item.id, outcome=label))
    was_due = item.due_at <= datetime.now(timezone.utc)
    extended = assistance == "independent" and outcome == "correct"
    retained = extended and was_due
    if retained:
        award_retained(db, user, item.competency_id, attempt.id)
    if extended:
        item.interval_days = _next_interval(item.interval_days)
    item.due_at = datetime.now(timezone.utc) + timedelta(days=item.interval_days)
    db.commit()
    db.refresh(item)
    return {
        "id": str(item.id),
        "outcome": outcome,
        "assistance": assistance,
        "interval_days": item.interval_days,
        "due_at": item.due_at.isoformat(),
        "extended": extended,
        "retained": retained,
    }


def snooze_review(
    db: Session,
    user: User,
    review_id: uuid.UUID,
    *,
    hours: int,
) -> dict[str, object]:
    """Move due_at by a duration. Interval and evidence stay untouched."""
    if hours < 1 or hours > 168:
        raise ApiError(
            "validation_error",
            "Snooze hours must be between 1 and 168",
            status_code=422,
        )
    item = get_owned_review(db, user, review_id)
    interval_before = item.interval_days
    item.due_at = datetime.now(timezone.utc) + timedelta(hours=hours)
    db.add(ReviewEvent(review_item_id=item.id, outcome="snooze"))
    db.commit()
    db.refresh(item)
    return {
        "id": str(item.id),
        "due_at": item.due_at.isoformat(),
        "interval_days": item.interval_days,
        "hours": hours,
        "retained": False,
        "extended": False,
        "unchanged_interval": item.interval_days == interval_before,
    }
