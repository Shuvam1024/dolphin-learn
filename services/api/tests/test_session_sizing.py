"""S66: target minutes size the sitting and remaining estimate."""

from __future__ import annotations

import uuid

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _auth(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _goal(headers: dict[str, str], preferred: int = 25) -> str:
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
                "preferred_session_minutes": preferred,
            },
        },
    )
    goal_id = created.json()["id"]
    client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    return goal_id


def test_target_minutes_default_and_override() -> None:
    headers = _auth("s66")
    goal_id = _goal(headers, preferred=30)
    defaulted = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    assert defaulted.status_code == 201
    assert defaulted.json()["target_minutes"] == 30
    studio = client.get(f"/api/v1/sessions/{defaulted.json()['id']}", headers=headers).json()
    assert studio["target_minutes"] == 30
    assert studio["remaining_estimate"]["low"] >= 1

    sized = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"goal_id": goal_id, "target_minutes": 15},
    )
    assert sized.status_code == 201
    assert sized.json()["target_minutes"] == 15
    body = client.get(f"/api/v1/sessions/{sized.json()['id']}", headers=headers).json()
    assert body["target_minutes"] == 15
    assert body["remaining_estimate"]["low"] <= 15 or body["remaining_estimate"]["low"] >= 1


def test_target_minutes_bounds() -> None:
    headers = _auth("s66-bounds")
    goal_id = _goal(headers)
    low = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"goal_id": goal_id, "target_minutes": 4},
    )
    assert low.status_code == 422
    high = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"goal_id": goal_id, "target_minutes": 181},
    )
    assert high.status_code == 422
