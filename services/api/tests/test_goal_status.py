"""S73: pause and archive goals; Home next action skips them."""

from __future__ import annotations

import uuid

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _goal(headers: dict[str, str]) -> str:
    with SessionLocal() as db:
        seed(db)
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 25,
            },
        },
    )
    goal_id = created.json()["id"]
    client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    return goal_id


def test_pause_and_archive_skip_home_next_action() -> None:
    headers = _headers("s73")
    goal_id = _goal(headers)
    home = client.get("/api/v1/home", headers=headers).json()
    assert home["next_action"]["kind"] == "start_session"
    assert home["next_action"]["goal_id"] == goal_id

    paused = client.patch(
        f"/api/v1/goals/{goal_id}",
        headers=headers,
        json={"status": "paused"},
    )
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"
    home_paused = client.get("/api/v1/home", headers=headers).json()
    assert home_paused["next_action"]["kind"] == "create_goal"
    assert home_paused["goals"][0]["status"] == "paused"

    resumed = client.patch(
        f"/api/v1/goals/{goal_id}",
        headers=headers,
        json={"status": "active"},
    )
    assert resumed.json()["status"] == "active"
    archived = client.patch(
        f"/api/v1/goals/{goal_id}",
        headers=headers,
        json={"status": "archived"},
    )
    assert archived.json()["status"] == "archived"
    home_arch = client.get("/api/v1/home", headers=headers).json()
    assert home_arch["next_action"]["kind"] == "create_goal"

    listed = client.get("/api/v1/goals", headers=headers).json()
    assert listed[0]["subject_name"]
    assert listed[0]["status"] == "archived"
    bad = client.patch(
        f"/api/v1/goals/{goal_id}",
        headers=headers,
        json={"status": "deleted"},
    )
    assert bad.status_code == 422
