"""S35: accepted path shows deferred work and resumes the right session."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def test_goal_overview_lists_deferred_work_and_continue_session() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s35-{uuid.uuid4().hex[:8]}@example.com"},
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
                "one_off_minutes": 15,
                "preferred_session_minutes": 15,
            },
        },
    )
    goal_id = created.json()["id"]
    client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    overview = client.get(f"/api/v1/goals/{goal_id}/overview", headers=headers)
    assert overview.status_code == 200
    body = overview.json()
    assert body["version_number"] == 1
    titles = [item["title"] for item in body["activities"]]
    assert titles[0].startswith("Names point at values")
    assert [item["position"] for item in body["activities"]] == list(
        range(1, len(body["activities"]) + 1)
    )
    assert body["activities"][0]["label"] == "prereq"
    deferred = {item["competency_key"]: item["reason_code"] for item in body["deferred"]}
    assert deferred["python.calls"] == "insufficient_minutes"
    assert body["why_next"].startswith("Why this next?")
    assert body["continue_action"]["kind"] == "start"
    assert body["continue_action"]["goal_id"] == goal_id

    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    again = client.get(f"/api/v1/goals/{goal_id}/overview", headers=headers)
    assert again.json()["continue_action"]["kind"] == "resume"
    assert again.json()["continue_action"]["href"] == f"/app/learn/{session_id}"

    other = client.post(
        "/api/v1/dev/token",
        json={"email": f"s35-other-{uuid.uuid4().hex[:8]}@example.com"},
    )
    hidden = client.get(
        f"/api/v1/goals/{goal_id}/overview",
        headers={"Authorization": f"Bearer {other.json()['access_token']}"},
    )
    assert hidden.status_code == 404
