"""S91: Effort calibration from measured active minutes."""

from __future__ import annotations

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.identity.models import User
from app.modules.learner_model.effort import (
    FACTOR_MAX,
    FACTOR_MIN,
    factor_for,
    record_observation,
)
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _user(headers: dict[str, str]) -> User:
    me = client.get("/api/v1/me", headers=headers).json()
    with SessionLocal() as db:
        user = db.get(User, uuid.UUID(me["id"]))
        assert user is not None
        db.expunge(user)
        return user


def test_factor_moves_toward_observed_ratio_and_clamps() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s91-ema")
    user = _user(headers)
    with SessionLocal() as db:
        user = db.merge(user)
        # Slow learner: observes 2x declared
        for _ in range(5):
            row = record_observation(
                db, user, "objective", observed_minutes=10, declared_low=5
            )
        assert row.observations >= 3
        assert FACTOR_MIN <= row.factor <= FACTOR_MAX
        assert row.factor > 1.0
        # Fast learner path for another type
        for _ in range(5):
            row = record_observation(
                db, user, "reading", observed_minutes=2, declared_low=8
            )
        assert row.factor < 1.0
        # Clamp high
        for _ in range(10):
            row = record_observation(
                db, user, "free_recall", observed_minutes=100, declared_low=5
            )
        assert row.factor == FACTOR_MAX


def test_factor_not_applied_under_three_observations() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s91-min")
    user = _user(headers)
    with SessionLocal() as db:
        user = db.merge(user)
        record_observation(db, user, "objective", observed_minutes=20, declared_low=5)
        record_observation(db, user, "objective", observed_minutes=20, declared_low=5)
        assert factor_for(db, user, "objective") == 1.0
        record_observation(db, user, "objective", observed_minutes=20, declared_low=5)
        assert factor_for(db, user, "objective") > 1.0


def test_slower_learner_120_plan_includes_fewer() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s91-plan")
    user = _user(headers)
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "names",
            "priority": "understand",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    before = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers)
    assert before.status_code == 200
    before_keys = [item["competency_key"] for item in before.json()["included"]]
    assert before_keys
    # Simulate a slow learner across common activity types
    with SessionLocal() as db:
        user = db.merge(user)
        for activity_type in ("reading", "objective", "short_answer", "free_recall", "worked_example", "reflection"):
            for _ in range(4):
                record_observation(
                    db, user, activity_type, observed_minutes=12, declared_low=4
                )
    after = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers)
    assert after.status_code == 200
    after_keys = [item["competency_key"] for item in after.json()["included"]]
    assert after.json()["usable_minutes"] == 120
    assert len(after_keys) <= len(before_keys)
    # Prerequisites stay intact: if conditionals is included, names and calls should be too
    if "python.conditionals" in after_keys:
        assert "python.names" in after_keys
        assert "python.calls" in after_keys
