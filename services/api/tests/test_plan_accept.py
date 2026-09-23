"""S25: a proposal stays inactive until the learner accepts version 1."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import PlanActivity, PlanVersion
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def test_accept_creates_version_one_and_lists_deferred() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s25-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names, then calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 15,
                "preferred_session_minutes": 15,
            },
        },
    )
    goal_id = created.json()["id"]
    proposed = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers, json={})
    assert proposed.status_code == 200
    missing = client.get(f"/api/v1/goals/{goal_id}/plan", headers=headers)
    assert missing.status_code == 404

    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    assert accepted.status_code == 201
    body = accepted.json()
    assert body["version_number"] == 1
    assert body["status"] == "accepted"
    assert "Calling a function" in body["rationale"]
    assert "Not enough minutes this time" in body["rationale"]
    assert "insufficient_minutes" not in body["rationale"]
    assert "python.calls" not in body["rationale"]
    assert any(item["title"].startswith("Names point at values") for item in body["activities"])

    refreshed = client.get(f"/api/v1/goals/{goal_id}/plan", headers=headers)
    assert refreshed.status_code == 200
    assert refreshed.json()["version_number"] == 1
    assert "Deferred:" in refreshed.json()["rationale"]

    with SessionLocal() as db:
        version = db.get(PlanVersion, uuid.UUID(body["id"]))
        assert version is not None
        count = db.scalar(
            select(func.count())
            .select_from(PlanActivity)
            .where(PlanActivity.plan_version_id == version.id)
        )
    assert count == len(body["activities"])
    assert count >= 1
