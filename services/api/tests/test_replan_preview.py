"""S75: replan previews before accept; stale hash is rejected."""

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import LearningPath, LearningSession, PlanVersion, SessionEvent
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def _study_minutes(session_id: str, minutes: int) -> None:
    start = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)
    pause_at = start + timedelta(minutes=minutes)
    finish_at = pause_at + timedelta(minutes=1)
    with SessionLocal() as db:
        row = db.get(LearningSession, uuid.UUID(session_id))
        assert row is not None
        row.started_at = start
        row.updated_at = finish_at
        for event in db.scalars(
            select(SessionEvent).where(SessionEvent.session_id == row.id)
        ).all():
            if event.event_type == "pause":
                event.created_at = pause_at
            elif event.event_type == "finish":
                event.created_at = finish_at
        db.commit()


def test_replan_preview_writes_nothing_then_accept_advances_version() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s75-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Fractions",
            "domain_key": "math",
            "raw_request": "Add fractions with the same denominator.",
            "time_budget": {
                "mode": "weekly",
                "weekly_minutes_per_day": 30,
                "horizon_days": 14,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    assert accepted.json()["version_number"] == 1
    assert accepted.json()["usable_minutes"] == 420

    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "pause-1", "event_type": "pause", "payload": {}}},
    )
    client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers)
    _study_minutes(session_id, 30)

    preview = client.post(f"/api/v1/goals/{goal_id}/replan-proposals", headers=headers)
    assert preview.status_code == 200
    body = preview.json()
    assert body["proposal_hash"]
    assert body["studied_minutes"] == 30
    assert body["remaining_minutes"] == 390
    assert body["usable_minutes"] == 390
    assert isinstance(body["included"], list)
    assert "priority_label" in body

    with SessionLocal() as db:
        versions = int(
            db.scalar(
                select(func.count())
                .select_from(PlanVersion)
                .join(LearningPath, PlanVersion.learning_path_id == LearningPath.id)
                .where(LearningPath.goal_id == uuid.UUID(goal_id))
            )
            or 0
        )
        assert versions == 1

    accepted_replan = client.post(
        f"/api/v1/goals/{goal_id}/replan/accept",
        headers=headers,
        json={"proposal_hash": body["proposal_hash"]},
    )
    assert accepted_replan.status_code == 200
    assert accepted_replan.json()["version_number"] == 2
    assert accepted_replan.json()["usable_minutes"] == 390

    overview = client.get(f"/api/v1/goals/{goal_id}/overview", headers=headers)
    assert overview.status_code == 200
    path = overview.json()
    assert path["remaining_minutes"] == 390
    assert path["studied_minutes"] == 30
    assert path["usable_minutes"] == 390  # plan version stores leftover at accept
    assert path["version_number"] == 2
    assert len(path["plan_history"]) >= 2
    first = path["activities"][0]
    assert "effort" in first
    assert "low" in first["effort"] and "high" in first["effort"]
    assert first["facet_label"]
    assert first["facet"]


def test_replan_accept_rejects_stale_proposal_hash() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s75-stale-{uuid.uuid4().hex[:8]}@example.com"},
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
    client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)

    preview = client.post(f"/api/v1/goals/{goal_id}/replan-proposals", headers=headers)
    assert preview.status_code == 200
    stale = preview.json()["proposal_hash"]

    client.patch(
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

    rejected = client.post(
        f"/api/v1/goals/{goal_id}/replan/accept",
        headers=headers,
        json={"proposal_hash": stale},
    )
    assert rejected.status_code == 409
    assert rejected.json()["error"]["code"] == "conflict"

    with SessionLocal() as db:
        versions = int(
            db.scalar(
                select(func.count())
                .select_from(PlanVersion)
                .join(LearningPath, PlanVersion.learning_path_id == LearningPath.id)
                .where(LearningPath.goal_id == uuid.UUID(goal_id))
            )
            or 0
        )
        assert versions == 1


def test_replan_preview_and_accept_are_owner_only() -> None:
    with SessionLocal() as db:
        seed(db)
    owner = client.post(
        "/api/v1/dev/token",
        json={"email": f"s75-own-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {owner.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 60,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    other = client.post(
        "/api/v1/dev/token",
        json={"email": f"s75-other-{uuid.uuid4().hex[:8]}@example.com"},
    )
    foreign = {"Authorization": f"Bearer {other.json()['access_token']}"}
    assert (
        client.post(f"/api/v1/goals/{goal_id}/replan-proposals", headers=foreign).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/goals/{goal_id}/replan/accept",
            headers=foreign,
            json={"proposal_hash": "deadbeef"},
        ).status_code
        == 404
    )
