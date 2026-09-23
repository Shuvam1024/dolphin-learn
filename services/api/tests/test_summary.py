"""S31: finish summarizes stored attempts and can be called twice."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import Attempt
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def test_finish_is_idempotent_and_pause_does_not_finish() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s31-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
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
                "preferred_session_minutes": 25,
            },
        },
    )
    goal_id = created.json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    question = next(
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    )
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]

    paused = client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "pause-open", "event_type": "pause", "payload": {}}},
    )
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"
    assert paused.json()["summary"] is None

    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "resume-open", "event_type": "resume", "payload": {}}},
    )
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "to-question",
                "event_type": "progress",
                "payload": {"plan_activity_id": question["id"]},
            }
        },
    )
    answered = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "once", "choice": "b"},
    )
    assert answered.json()["outcome"] == "correct"

    first = client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers)
    assert first.status_code == 200
    body = first.json()
    assert body["status"] == "finished"
    assert body["summary"]["note"].startswith("This summary counts stored attempts only")
    assert len(body["summary"]["independent_attempts"]) == 1
    assert body["summary"]["independent_attempts"][0]["attempt_id"] == answered.json()["id"]
    assert body["summary"]["independent_attempts"][0]["outcome"] == "correct"
    assert any(
        item["competency_key"] == "python.names" for item in body["summary"]["suggested_review"]
    )
    assert "Not retention" in body["summary"]["suggested_review"][0]["reason"]

    second = client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers)
    again = second.json()["summary"]["independent_attempts"]
    assert again == body["summary"]["independent_attempts"]
    with SessionLocal() as db:
        count = db.scalar(
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.session_id == uuid.UUID(session_id))
        )
    assert count == 1

    blocked = client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "pause-after", "event_type": "pause", "payload": {}}},
    )
    assert blocked.status_code == 422
    still = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert still.json()["status"] == "finished"
