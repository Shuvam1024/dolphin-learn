"""Heavy learner fixture for API latency budgets (S51)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from app.db import SessionLocal
from app.main import app
from app.modules.curriculum.models import Competency
from app.modules.learning.models import ActivityVersion, Attempt, Lesson, ReviewItem
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


@pytest.fixture(scope="module")
def api_client() -> TestClient:
    return client


@pytest.fixture(scope="module")
def heavy_learner() -> dict[str, object]:
    """5 goals, 3 plan versions on the first, 60 attempts, 20 review items."""
    with SessionLocal() as db:
        seed(db)

    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s51-perf-{uuid.uuid4().hex[:8]}@example.com"},
    )
    assert issued.status_code == 200
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    me = client.get("/api/v1/me", headers=headers)
    user_id = me.json()["id"]

    goal_ids: list[str] = []
    for index in range(5):
        domain = "python" if index % 2 == 0 else "math"
        created = client.post(
            "/api/v1/goals",
            headers=headers,
            json={
                "title": f"Perf goal {index}",
                "domain_key": domain,
                "raw_request": f"Perf load for domain {domain}.",
                "time_budget": {
                    "mode": "one_off",
                    "one_off_minutes": 120,
                    "preferred_session_minutes": 30,
                },
            },
        )
        assert created.status_code == 201, created.text
        goal_id = created.json()["id"]
        goal_ids.append(goal_id)
        accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
        assert accepted.status_code == 201, accepted.text

    first = goal_ids[0]
    for minutes in (90, 60):
        patched = client.patch(
            f"/api/v1/goals/{first}",
            headers=headers,
            json={
                "time_budget": {
                    "mode": "one_off",
                    "one_off_minutes": minutes,
                    "preferred_session_minutes": 30,
                }
            },
        )
        assert patched.status_code == 200
        replan = client.post(f"/api/v1/goals/{first}/replan", headers=headers)
        assert replan.status_code in (200, 201), replan.text
        assert replan.json()["version_number"] >= 2

    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": first})
    assert started.status_code == 201, started.text
    session_id = started.json()["id"]
    plan = client.get(f"/api/v1/goals/{first}/plan", headers=headers)
    activities = plan.json()["activities"]
    question = next(item for item in activities if item["title"].endswith("objective"))
    moved = client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "perf-to-q",
                "event_type": "progress",
                "payload": {"plan_activity_id": question["id"]},
            }
        },
    )
    assert moved.status_code == 200, moved.text

    for index in range(60):
        attempt = client.post(
            f"/api/v1/sessions/{session_id}/attempts",
            headers=headers,
            json={"idempotency_key": f"perf-attempt-{index}", "choice": "b"},
        )
        assert attempt.status_code == 200, attempt.text

    with SessionLocal() as db:
        competency_ids = list(
            db.scalars(
                select(Competency.id)
                .join(Lesson, Lesson.competency_id == Competency.id)
                .join(ActivityVersion, ActivityVersion.lesson_id == Lesson.id)
                .where(ActivityVersion.activity_type == "objective")
                .distinct()
                .limit(5)
            )
        )
        assert competency_ids
        for index in range(20):
            db.add(
                ReviewItem(
                    user_id=uuid.UUID(user_id),
                    competency_id=competency_ids[index % len(competency_ids)],
                    interval_days=1,
                    due_at=datetime.now(timezone.utc) - timedelta(hours=1),
                )
            )
        db.commit()
        attempt_count = db.scalar(
            select(func.count()).select_from(Attempt).where(Attempt.user_id == uuid.UUID(user_id))
        )
        assert attempt_count is not None and attempt_count >= 60

    due = client.get("/api/v1/reviews/due", headers=headers)
    assert due.status_code == 200, due.text
    home = client.get("/api/v1/home", headers=headers)
    assert home.status_code == 200, home.text

    return {
        "headers": headers,
        "goal_id": first,
        "session_id": session_id,
        "goal_ids": goal_ids,
    }
