"""Study time is minutes a session was active. Time away does not count."""

import os
from datetime import datetime, timedelta, timezone

from app.modules.goals.models import Goal
from app.modules.identity.models import User
from app.modules.learning.models import (
    LearningPath,
    LearningSession,
    PlanActivity,
    PlanVersion,
    SessionEvent,
)
from sqlalchemy import select
from sqlalchemy.orm import Session


def active_minutes(
    started_at: datetime,
    events: list[tuple[datetime, str]],
    *,
    now: datetime,
) -> int:
    """Whole minutes from start→pause and resume→pause or finish. Floor, never negative."""
    cursor = started_at
    running = True
    stopped = False
    total = timedelta(0)
    for created_at, event_type in events:
        if stopped:
            break
        mark = created_at if created_at > cursor else cursor
        if event_type == "pause" and running:
            total += mark - cursor
            running = False
            cursor = mark
        elif event_type == "resume" and not running:
            running = True
            cursor = mark
        elif event_type == "finish":
            if running:
                total += mark - cursor
            running = False
            stopped = True
            cursor = mark
    if running and not stopped and now > cursor:
        total += now - cursor
    seconds = int(total.total_seconds())
    if seconds < 0:
        return 0
    # E2E only: one wall-clock second counts as one active minute so stop-point
    # flows can be exercised without sleeping for real sittings.
    if os.environ.get("DOLPHIN_E2E_FAST_CLOCK") == "1":
        return seconds
    return seconds // 60


def session_active_minutes(
    db: Session,
    row: LearningSession,
    *,
    now: datetime | None = None,
) -> int:
    clock = now or datetime.now(timezone.utc)
    stored = db.scalars(
        select(SessionEvent)
        .where(SessionEvent.session_id == row.id)
        .order_by(SessionEvent.created_at, SessionEvent.id)
    ).all()
    events = [(event.created_at, event.event_type) for event in stored]
    finished = any(kind == "finish" for _, kind in events)
    end = row.updated_at if row.status == "finished" and not finished else clock
    return active_minutes(row.started_at, events, now=end)


def sessions_for_goal(db: Session, user: User, goal: Goal) -> list[LearningSession]:
    """Every session on any plan version of this goal."""
    rows = db.scalars(
        select(LearningSession)
        .join(PlanActivity, LearningSession.plan_activity_id == PlanActivity.id)
        .join(PlanVersion, PlanActivity.plan_version_id == PlanVersion.id)
        .join(LearningPath, PlanVersion.learning_path_id == LearningPath.id)
        .where(
            LearningSession.user_id == user.id,
            LearningPath.goal_id == goal.id,
        )
        .order_by(LearningSession.started_at, LearningSession.id)
    ).all()
    return list(rows)


def studied_minutes_for_goal(
    db: Session,
    user: User,
    goal: Goal,
    *,
    now: datetime | None = None,
) -> int:
    return sum(
        session_active_minutes(db, row, now=now) for row in sessions_for_goal(db, user, goal)
    )


def remaining_minutes(usable: int, studied: int) -> int:
    left = usable - studied
    return left if left > 0 else 0
