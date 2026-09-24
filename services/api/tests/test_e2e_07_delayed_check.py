"""E2E-07: a delayed check records delay (test clock).

Gate 6 acceptance: when exposure and the later attempt are separated by a
controllable clock, `v_attempt_features.delay_since_exposure_minutes` is
positive and matches the elapsed minutes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.identity.models import User
from app.modules.learning.models import (
    ActivityVersion,
    Attempt,
    Evaluation,
    LearningSession,
    Lesson,
    SessionEvent,
)
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select, text

client = TestClient(app)


class DelayClock:
    """Controllable clock for delay assertions (no freezegun dependency)."""

    def __init__(self, start: datetime | None = None) -> None:
        self.now = start or datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    def advance(self, *, minutes: int = 0, hours: int = 0, days: int = 0) -> datetime:
        self.now = self.now + timedelta(minutes=minutes, hours=hours, days=days)
        return self.now


def test_e2e_07_delayed_check_records_delay() -> None:
    with SessionLocal() as db:
        seed(db)

    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"e2e07-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    me = client.get("/api/v1/me", headers=headers).json()
    user_id = uuid.UUID(me["id"])

    clock = DelayClock()
    exposed_at = clock.now
    clock.advance(hours=26)
    attempted_at = clock.now
    expected_minutes = (attempted_at - exposed_at).total_seconds() / 60.0

    with SessionLocal() as db:
        user = db.get(User, user_id)
        assert user is not None
        activity = db.scalar(
            select(ActivityVersion)
            .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
            .where(
                ActivityVersion.activity_type == "objective",
                ActivityVersion.source == "seed",
                ActivityVersion.provisional.is_(False),
            )
            .limit(1)
        )
        assert activity is not None
        session = LearningSession(user_id=user.id, status="active")
        db.add(session)
        db.flush()
        db.add(
            SessionEvent(
                session_id=session.id,
                client_event_id="e2e07-expose",
                event_type="progress",
                payload={"activity_version_id": str(activity.id)},
                created_at=exposed_at,
            )
        )
        attempt = Attempt(
            user_id=user.id,
            activity_version_id=activity.id,
            session_id=session.id,
            response={"choice": "b", "assistance": "independent"},
            submitted_at=attempted_at,
        )
        db.add(attempt)
        db.flush()
        db.add(
            Evaluation(
                attempt_id=attempt.id,
                score=1,
                assistance="independent",
                outcome="correct",
                evaluator="test",
            )
        )
        attempt_id = attempt.id
        db.commit()

    with SessionLocal() as db:
        row = db.execute(
            text(
                "SELECT delay_since_exposure_minutes FROM v_attempt_features "
                "WHERE attempt_id = :aid"
            ),
            {"aid": attempt_id},
        ).first()
        assert row is not None
        delay = float(row[0])
        assert delay >= expected_minutes - 1
        assert delay <= expected_minutes + 1
        assert delay >= 24 * 60  # at least one day later
