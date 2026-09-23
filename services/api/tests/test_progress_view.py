"""S34: progress lists facets and unassessed plan gaps, never a mastery percent."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def test_progress_facets_match_evidence_and_leave_gaps_unassessed() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s34-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    empty = client.get("/api/v1/progress", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["facets"] == []
    assert empty.json()["unassessed"] == []
    assert "mastered" not in empty.text
    assert "%" not in empty.text

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
    questions = [
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    ]
    planned = client.get("/api/v1/progress", headers=headers)
    unassessed = {item["competency_key"] for item in planned.json()["unassessed"]}
    assert unassessed == {"python.names", "python.calls", "python.conditionals"}
    assert planned.json()["facets"] == []

    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "to-q",
                "event_type": "progress",
                "payload": {"plan_activity_id": questions[0]["id"]},
            }
        },
    )
    client.post(
        f"/api/v1/sessions/{session_id}/solution",
        headers=headers,
        json={"mode": "guided"},
    )
    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "helped", "choice": "b"},
    )
    practiced = client.get("/api/v1/progress", headers=headers)
    facets = {item["competency_key"]: item["status_facet"] for item in practiced.json()["facets"]}
    assert facets["python.names"] == "practicing"
    still = {item["competency_key"] for item in practiced.json()["unassessed"]}
    assert "python.calls" in still
    assert "python.names" not in still
    assert "mastered" not in practiced.text
