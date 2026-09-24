"""S67: stop point when active minutes reach the sitting target."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import LearningSession
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _auth(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def test_stop_point_when_active_reaches_target() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _auth("s67")
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
    started = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"goal_id": goal_id, "target_minutes": 10},
    )
    session_id = started.json()["id"]
    before = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert before["actions"]["stop_point"] is False

    with SessionLocal() as db:
        row = db.get(LearningSession, uuid.UUID(session_id))
        assert row is not None
        row.started_at = datetime.now(timezone.utc) - timedelta(minutes=12)
        db.commit()

    after = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert after["active_minutes"] >= 10
    assert after["actions"]["stop_point"] is True
    assert after["actions"]["primary"] == "finish"
    assert after["actions"]["can_keep_going"] is True
