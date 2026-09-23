"""S36: replan after a budget edit writes version N+1 and leaves attempts alone."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import Attempt, LearningPath, PlanVersion
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def test_replan_after_budget_edit_creates_next_version_without_touching_attempts() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s36-{uuid.uuid4().hex[:8]}@example.com"},
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
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    assert accepted.json()["version_number"] == 1
    questions = [
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    ]
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
    me = client.get("/api/v1/me", headers=headers)
    user_id = uuid.UUID(me.json()["id"])
    goal_uuid = uuid.UUID(goal_id)

    def counts() -> tuple[int, int]:
        with SessionLocal() as db:
            attempts = db.scalar(
                select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id)
            )
            versions = db.scalar(
                select(func.count())
                .select_from(PlanVersion)
                .join(LearningPath, PlanVersion.learning_path_id == LearningPath.id)
                .where(LearningPath.goal_id == goal_uuid)
            )
            return int(attempts or 0), int(versions or 0)

    before_attempts, before_versions = counts()
    assert before_attempts == 1
    assert before_versions == 1

    patched = client.patch(
        f"/api/v1/goals/{goal_id}",
        headers=headers,
        json={
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 15,
                "preferred_session_minutes": 15,
            }
        },
    )
    assert patched.status_code == 200
    replanned = client.post(f"/api/v1/goals/{goal_id}/replan", headers=headers)
    assert replanned.status_code == 200
    body = replanned.json()
    assert body["version_number"] == 2
    assert "insufficient_minutes" in body["rationale"]
    assert "Already demonstrated: python.names" in body["rationale"]
    assert "still need an explicit accept" in body["rationale"]

    proposed = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers)
    assert proposed.status_code == 200
    after_attempts, after_versions = counts()
    assert after_attempts == before_attempts
    assert after_versions == 2

    with SessionLocal() as db:
        first = db.scalar(
            select(PlanVersion)
            .join(LearningPath, PlanVersion.learning_path_id == LearningPath.id)
            .where(LearningPath.goal_id == goal_uuid, PlanVersion.version_number == 1)
        )
        assert first is not None
        assert first.rationale != body["rationale"]

    current = client.get(f"/api/v1/goals/{goal_id}/plan", headers=headers)
    assert current.json()["version_number"] == 2
    other = client.post(
        "/api/v1/dev/token",
        json={"email": f"s36-other-{uuid.uuid4().hex[:8]}@example.com"},
    )
    hidden = client.post(
        f"/api/v1/goals/{goal_id}/replan",
        headers={"Authorization": f"Bearer {other.json()['access_token']}"},
    )
    assert hidden.status_code == 404
