"""S26: a session resumes from stored events, and a repeated event id is a no-op."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import SessionEvent
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def test_start_pause_and_ignore_duplicate_event() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s26-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    other = client.post(
        "/api/v1/dev/token",
        json={"email": f"s26-other-{uuid.uuid4().hex[:8]}@example.com"},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}

    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names and calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    assert accepted.status_code == 201
    activities = accepted.json()["activities"]
    assert len(activities) >= 2
    first_id = activities[0]["id"]
    second_id = activities[1]["id"]

    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    assert started.status_code == 201
    session_id = started.json()["id"]
    assert started.json()["plan_activity_id"] == first_id
    assert started.json()["status"] == "active"
    activity = started.json()["activity"]
    assert activity["activity_type"] == "reading"
    assert activity["mode"] == "guided"
    assert "binds the name" in activity["body"]
    assert "answer_key" not in started.text

    moved = client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "progress-1",
                "event_type": "progress",
                "payload": {"plan_activity_id": second_id},
            }
        },
    )
    assert moved.status_code == 200
    assert moved.json()["applied"] is True
    assert moved.json()["plan_activity_id"] == second_id

    refreshed = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert refreshed.status_code == 200
    assert refreshed.json()["plan_activity_id"] == second_id
    assert refreshed.json()["event_count"] == 1

    duplicate = client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "progress-1",
                "event_type": "progress",
                "payload": {"plan_activity_id": first_id},
            }
        },
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["applied"] is False
    assert duplicate.json()["plan_activity_id"] == second_id
    assert duplicate.json()["event_count"] == 1

    paused = client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "pause-1", "event_type": "pause", "payload": {}}},
    )
    assert paused.json()["status"] == "paused"
    again = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert again.json()["status"] == "paused"
    assert again.json()["plan_activity_id"] == second_id

    hidden = client.get(f"/api/v1/sessions/{session_id}", headers=other_headers)
    assert hidden.status_code == 404

    with SessionLocal() as db:
        count = db.scalar(
            select(func.count())
            .select_from(SessionEvent)
            .where(SessionEvent.session_id == uuid.UUID(session_id))
        )
    assert count == 2
