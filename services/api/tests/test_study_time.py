"""S43: study minutes count only while a session is active."""

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import LearningSession, SessionEvent
from app.modules.learning.study_time import active_minutes
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


def test_pause_gap_is_excluded_and_finish_freezes_the_total() -> None:
    start = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)
    pause_at = start + timedelta(minutes=10)
    resume_at = pause_at + timedelta(minutes=30)
    finish_at = resume_at + timedelta(minutes=5)
    later = finish_at + timedelta(hours=3)
    events = [
        (pause_at, "pause"),
        (resume_at, "resume"),
        (finish_at, "finish"),
    ]
    assert active_minutes(start, events, now=later) == 15
    paused = [(pause_at, "pause"), (pause_at, "pause")]
    assert active_minutes(start, paused, now=later) == 10


def test_session_clock_ignores_time_away() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s43-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "raw_request": "Names and calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    assert started.json()["active_minutes"] == 0

    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "pause-1", "event_type": "pause", "payload": {}}},
    )
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "pause-1", "event_type": "pause", "payload": {}}},
    )
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "resume-1", "event_type": "resume", "payload": {}}},
    )
    finished = client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers)
    assert finished.status_code == 200

    start = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)
    pause_at = start + timedelta(minutes=10)
    resume_at = pause_at + timedelta(minutes=30)
    finish_at = resume_at + timedelta(minutes=5)
    with SessionLocal() as db:
        row = db.get(LearningSession, uuid.UUID(session_id))
        assert row is not None
        row.started_at = start
        row.updated_at = finish_at
        saved = db.scalars(
            select(SessionEvent)
            .where(SessionEvent.session_id == row.id)
            .order_by(SessionEvent.created_at, SessionEvent.id)
        ).all()
        stamps = {
            "pause": pause_at,
            "resume": resume_at,
            "finish": finish_at,
        }
        for event in saved:
            if event.event_type in stamps:
                event.created_at = stamps[event.event_type]
        db.commit()

    again = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert again.status_code == 200
    assert again.json()["active_minutes"] == 15
    assert again.json()["status"] == "finished"
    assert "deadline" not in again.text
