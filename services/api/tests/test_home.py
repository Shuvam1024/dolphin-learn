"""S33: Home shows the next real action, not a placeholder or a streak."""

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import ReviewItem
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def test_home_empty_then_live_next_action_without_streak() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s33")
    empty = client.get("/api/v1/home", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["next_action"]["kind"] == "create_goal"
    assert empty.json()["next_action"]["href"] == "/app/goals/new"
    assert empty.json()["goals"] == []
    assert empty.json()["quick_learn"]["label"] == "Quick Learn"
    assert empty.json()["due_reviews"]["count"] == 0
    assert "streak" not in empty.text
    assert "mastered" not in empty.text

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
    questions = [
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    ]
    planned = client.get("/api/v1/home", headers=headers)
    assert planned.json()["next_action"]["kind"] == "start_session"
    assert planned.json()["next_action"]["goal_id"] == goal_id
    assert "/start" in planned.json()["next_action"]["href"]
    assert "Usable minutes: 120" in planned.json()["goals"][0]["feasibility_note"]
    assert "Deferred: none" in planned.json()["goals"][0]["feasibility_note"]
    assert planned.json()["goals"][0]["subject_name"]
    assert planned.json()["goals"][0]["next_lesson_title"]

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
    # Resolve correct choice from the plan activity via studio after jump
    studio = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    choice = "b"
    if studio.get("studio_activity") and studio["studio_activity"].get("choices"):
        # Prefer letter that matches seeded names answer when present
        ids = [c["id"] for c in studio["studio_activity"]["choices"]]
        choice = "b" if "b" in ids else ids[0]
    from app.modules.learning.models import ActivityVersion, PlanActivity

    with SessionLocal() as db:
        plan = db.get(PlanActivity, uuid.UUID(questions[0]["id"]))
        assert plan is not None and plan.activity_version_id is not None
        activity = db.get(ActivityVersion, plan.activity_version_id)
        assert activity is not None and activity.answer_key is not None
        choice = str(activity.answer_key.get("correct", choice))
    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "once", "choice": choice},
    )
    me = client.get("/api/v1/me", headers=headers)
    user_id = uuid.UUID(me.json()["id"])
    with SessionLocal() as db:
        item = db.scalar(select(ReviewItem).where(ReviewItem.user_id == user_id))
        assert item is not None
        item.due_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()

    live = client.get("/api/v1/home", headers=headers)
    body = live.json()
    assert body["next_action"]["kind"] == "review"
    assert body["next_action"]["href"] == "/app/review"
    assert body["due_reviews"]["count"] == 1
    assert body["due_reviews"]["items"][0]["competency_key"] == "python.names"
    assert "Not retention" in body["due_reviews"]["items"][0]["reason"]
    assert body["recent_evidence"][0]["competency_key"] == "python.names"
    assert body["recent_evidence"][0]["facet_label"] == "Shown on your own"
    assert "streak" not in live.text

    other = client.get("/api/v1/home", headers=_headers("s33-other"))
    assert other.json()["goals"] == []
    assert other.json()["due_reviews"]["count"] == 0
