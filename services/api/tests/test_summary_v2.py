"""S68: honest session summary v2 — showed, practiced, self-reported, next."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import ActivityVersion, PlanActivity
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)

_FORBIDDEN = re.compile(
    r"streak|congratulations|great job|well done|mastery\s*%|you('re| are) (on fire|crushing)",
    re.I,
)


def _auth(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _correct_for_plan(plan_activity_id: str) -> str:
    with SessionLocal() as db:
        plan = db.get(PlanActivity, uuid.UUID(plan_activity_id))
        assert plan is not None and plan.activity_version_id is not None
        activity = db.get(ActivityVersion, plan.activity_version_id)
        assert activity is not None and activity.answer_key is not None
        return str(activity.answer_key.get("correct", ""))


def test_summary_v2_buckets_and_next_step() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _auth("s68")
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
                "preferred_session_minutes": 25,
            },
        },
    )
    goal_id = created.json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    question = next(
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    )
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "to-q",
                "event_type": "progress",
                "payload": {"plan_activity_id": question["id"]},
            }
        },
    )
    correct = _correct_for_plan(question["id"])
    answered = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "s68-once", "choice": correct},
    )
    assert answered.status_code == 200
    assert answered.json()["outcome"] == "correct"
    finished = client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers)
    assert finished.status_code == 200
    summary = finished.json()["summary"]
    assert len(summary["showed_on_your_own"]) == 1
    assert summary["showed_on_your_own"][0]["outcome"] == "correct"
    assert summary["practiced_with_help"] == []
    assert isinstance(summary["self_reported"], list)
    assert isinstance(summary["watch_out_for"], list)
    assert isinstance(summary["minutes_studied"], int)
    assert summary["next_step"]["href"] == f"/app/goals/{goal_id}"
    assert summary["next_step"]["label"]
    assert _FORBIDDEN.search(summary["note"]) is None
    for bucket in (
        summary["showed_on_your_own"],
        summary["practiced_with_help"],
        summary["self_reported"],
        summary["watch_out_for"],
    ):
        for item in bucket:
            blob = " ".join(str(item.get(key, "")) for key in item)
            assert _FORBIDDEN.search(blob) is None


def test_summary_v2_forbidden_words_in_module() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "app/modules/learning/summary.py").read_text()
    assert _FORBIDDEN.search(text) is None
    assert "celebration" not in text.lower()
