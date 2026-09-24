"""S77: progress grouped by goal with chips and upcoming reviews."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def test_progress_v2_groups_by_goal_without_percent() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s77-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    empty = client.get("/api/v1/progress", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["goals"] == []
    assert empty.json()["upcoming_reviews"] == []
    assert "%" not in empty.text
    assert "mastered" not in empty.text

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
    questions = [
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    ]

    planned = client.get("/api/v1/progress", headers=headers)
    body = planned.json()
    assert len(body["goals"]) == 1
    group = body["goals"][0]
    assert group["id"] == goal_id
    assert group["title"] == "Learn Python"
    assert group["unassessed_count"] >= 2
    names = {item["name"] for item in group["competencies"]}
    assert "Names and values" in names
    assert all(item["facet"] == "unassessed" for item in group["competencies"])
    assert all(item["facet_label"] == "Not tried yet" for item in group["competencies"])
    assert "%" not in planned.text

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
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "once", "choice": "b"},
    )

    after = client.get("/api/v1/progress", headers=headers).json()
    group = after["goals"][0]
    by_name = {item["name"]: item for item in group["competencies"]}
    names_row = by_name["Names and values"]
    assert names_row["facet"] == "independently_demonstrated"
    assert names_row["facet_label"] == "Shown on your own"
    assert names_row["last_independent_at"]
    assert names_row["self_reported"] is False
    assert group["unassessed_count"] >= 1
    assert isinstance(after["upcoming_reviews"], list)
    assert "%" not in client.get("/api/v1/progress", headers=headers).text
