"""S44: studied minutes sit beside the usable budget, not as a score."""

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import LearningSession, SessionEvent
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


def test_studied_minutes_sit_beside_a_weekly_budget() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s44-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Fractions",
            "raw_request": "Add fractions with the same denominator.",
            "time_budget": {
                "mode": "weekly",
                "weekly_minutes_per_day": 30,
                "horizon_days": 14,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "pause-1", "event_type": "pause", "payload": {}}},
    )
    client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers)

    start = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)
    pause_at = start + timedelta(minutes=30)
    finish_at = pause_at + timedelta(minutes=1)
    with SessionLocal() as db:
        row = db.get(LearningSession, uuid.UUID(session_id))
        assert row is not None
        row.started_at = start
        row.updated_at = finish_at
        for event in db.scalars(
            select(SessionEvent)
            .where(SessionEvent.session_id == row.id)
            .order_by(SessionEvent.created_at, SessionEvent.id)
        ).all():
            if event.event_type == "pause":
                event.created_at = pause_at
            elif event.event_type == "finish":
                event.created_at = finish_at
        db.commit()

    overview = client.get(f"/api/v1/goals/{goal_id}/overview", headers=headers)
    assert overview.status_code == 200
    body = overview.json()
    assert body["usable_minutes"] == 420
    assert body["studied_minutes"] == 30
    assert "%" not in overview.text
    assert "mastered" not in overview.text
    assert "deadline" not in overview.text

    home = client.get("/api/v1/home", headers=headers)
    card = home.json()["goals"][0]
    assert card["usable_minutes"] == 420
    assert card["studied_minutes"] == 30
    assert "%" not in home.text
    assert "deadline" not in home.text
