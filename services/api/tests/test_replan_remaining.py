"""S45: replan fits the minutes still available after study."""

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.goals.models import TimeBudget
from app.modules.learning.models import (
    Attempt,
    CompetencyEvidence,
    LearningPath,
    LearningSession,
    PlanVersion,
    SessionEvent,
)
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def test_replan_uses_remaining_minutes_and_leaves_budget_and_evidence() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s45-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Fractions",
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
    assert accepted.json()["usable_minutes"] == 420
    assert accepted.json()["version_number"] == 1
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "pause-1", "event_type": "pause", "payload": {}}},
    )
    client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers)

    start = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)
    pause_at = start + timedelta(minutes=30)
    finish_at = pause_at + timedelta(minutes=1)
    me = client.get("/api/v1/me", headers=headers)
    user_id = uuid.UUID(me.json()["id"])
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
        evidence_before = int(
            db.scalar(
                select(func.count())
                .select_from(CompetencyEvidence)
                .where(CompetencyEvidence.user_id == user_id)
            )
            or 0
        )
        attempts_before = int(
            db.scalar(
                select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id)
            )
            or 0
        )
        db.commit()

    replanned = client.post(f"/api/v1/goals/{goal_id}/replan", headers=headers)
    assert replanned.status_code == 200
    body = replanned.json()
    assert body["version_number"] == 2
    assert body["usable_minutes"] == 390
    assert "Studied minutes: 30" in body["rationale"]
    assert "Remaining minutes: 390" in body["rationale"]
    assert "original budget is unchanged" in body["rationale"]

    with SessionLocal() as db:
        budget = db.scalar(
            select(TimeBudget).where(TimeBudget.goal_id == uuid.UUID(goal_id))
        )
        assert budget is not None
        assert budget.weekly_minutes_per_day == 30
        assert budget.horizon_days == 14
        versions = int(
            db.scalar(
                select(func.count())
                .select_from(PlanVersion)
                .join(LearningPath, PlanVersion.learning_path_id == LearningPath.id)
                .where(LearningPath.goal_id == uuid.UUID(goal_id))
            )
            or 0
        )
        assert versions == 2
        evidence_after = int(
            db.scalar(
                select(func.count())
                .select_from(CompetencyEvidence)
                .where(CompetencyEvidence.user_id == user_id)
            )
            or 0
        )
        attempts_after = int(
            db.scalar(
                select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id)
            )
            or 0
        )
        assert evidence_after == evidence_before
        assert attempts_after == attempts_before

    overview = client.get(f"/api/v1/goals/{goal_id}/overview", headers=headers)
    assert overview.json()["usable_minutes"] == 390
    assert overview.json()["studied_minutes"] == 30
    assert overview.json()["version_number"] == 2


def test_replan_with_no_minutes_left_is_a_scope_conflict() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s45-zero-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "raw_request": "Names and calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 30,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"event": {"client_event_id": "pause-1", "event_type": "pause", "payload": {}}},
    )
    client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers)
    start = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)
    pause_at = start + timedelta(minutes=30)
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

    replanned = client.post(f"/api/v1/goals/{goal_id}/replan", headers=headers)
    body = replanned.json()
    assert body["usable_minutes"] == 0
    assert "Remaining minutes: 0" in body["rationale"]
    assert "Scope conflict" in body["rationale"]
