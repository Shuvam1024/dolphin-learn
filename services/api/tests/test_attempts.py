"""S28: an objective answer is stored once per idempotency key."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import Attempt
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def _open_question() -> tuple[dict[str, str], dict[str, str], str]:
    with SessionLocal() as db:
        seed(db)
    owner = client.post(
        "/api/v1/dev/token",
        json={"email": f"s28-{uuid.uuid4().hex[:8]}@example.com"},
    )
    other = client.post(
        "/api/v1/dev/token",
        json={"email": f"s28-other-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {owner.json()['access_token']}"}
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
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
    moved = client.patch(
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
    assert moved.status_code == 200
    assert moved.json()["activity"]["activity_type"] == "objective"
    return headers, other_headers, session_id


def test_same_idempotency_key_returns_the_same_attempt() -> None:
    headers, other_headers, session_id = _open_question()
    body = {"idempotency_key": "answer-1", "choice": "b"}
    first = client.post(f"/api/v1/sessions/{session_id}/attempts", headers=headers, json=body)
    assert first.status_code == 200
    assert first.json()["created"] is True
    assert first.json()["choice"] == "b"
    assert first.json()["assistance"] == "independent"
    assert "n = 3" in first.json()["prompt"]

    second = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "answer-1", "choice": "a"},
    )
    assert second.status_code == 200
    assert second.json()["created"] is False
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["choice"] == "b"

    denied = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=other_headers,
        json=body,
    )
    assert denied.status_code == 404

    with SessionLocal() as db:
        count = db.scalar(
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.session_id == uuid.UUID(session_id))
        )
    assert count == 1
