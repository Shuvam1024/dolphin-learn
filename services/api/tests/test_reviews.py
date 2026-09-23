"""S32: independent success schedules a future review; assisted success does not extend it."""

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import ReviewItem
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


def _auth(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _python_session(headers: dict[str, str]) -> tuple[str, list[dict[str, str]]]:
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
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    return started.json()["id"], questions


def _answer(
    headers: dict[str, str],
    session_id: str,
    activity_id: str,
    key: str,
    choice: str,
) -> None:
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": key,
                "event_type": "progress",
                "payload": {"plan_activity_id": activity_id},
            }
        },
    )
    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": key, "choice": choice},
    )


def test_independent_success_schedules_future_due_and_review_updates_it() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _auth("s32")
    session_id, questions = _python_session(headers)
    _answer(headers, session_id, questions[0]["id"], "first", "b")
    me = client.get("/api/v1/me", headers=headers)
    user_id = uuid.UUID(me.json()["id"])

    with SessionLocal() as db:
        item = db.scalar(select(ReviewItem).where(ReviewItem.user_id == user_id))
        assert item is not None
        assert item.interval_days == 1
        assert item.due_at > datetime.now(timezone.utc)
        item.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
        review_id = str(item.id)
        db.commit()

    due = client.get("/api/v1/reviews/due", headers=headers)
    assert due.status_code == 200
    body = due.json()
    assert body["due"][0]["competency_key"] == "python.names"
    assert "Not retention" in body["due"][0]["reason"]
    assert "answer_key" not in body["due"][0]
    assert body["due"][0]["revealed_choice"] == ""

    other = _auth("s32-other")
    hidden = client.post(
        f"/api/v1/reviews/{review_id}/attempts",
        headers=other,
        json={"choice": "b"},
    )
    assert hidden.status_code == 404

    done = client.post(
        f"/api/v1/reviews/{review_id}/attempts",
        headers=headers,
        json={"choice": "b"},
    )
    assert done.status_code == 200
    assert done.json()["assistance"] == "independent"
    assert done.json()["extended"] is True
    assert done.json()["interval_days"] == 3
    later = datetime.fromisoformat(done.json()["due_at"])
    assert later > datetime.now(timezone.utc) + timedelta(days=2)


def test_assisted_path_does_not_schedule_or_extend() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _auth("s32-assisted")
    session_id, questions = _python_session(headers)
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
        f"/api/v1/sessions/{session_id}/solution",
        headers=headers,
        json={"mode": "guided"},
    )
    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "helped", "choice": "b"},
    )
    empty = client.get("/api/v1/reviews/due", headers=headers)
    assert empty.json()["due"] == []
    assert empty.json()["scheduled"] == []

    _answer(headers, session_id, questions[1]["id"], "alone", "a")
    queued = client.get("/api/v1/reviews/due", headers=headers)
    scheduled = queued.json()["scheduled"]
    assert len(scheduled) == 1
    assert scheduled[0]["interval_days"] == 1
    review_id = scheduled[0]["id"]
    before = scheduled[0]["due_at"]

    _answer(headers, session_id, questions[2]["id"], "again", "b")
    again = client.get("/api/v1/reviews/due", headers=headers)
    assert again.json()["scheduled"][0]["interval_days"] == 1
    assert again.json()["scheduled"][0]["due_at"] == before

    blocked = client.post(
        f"/api/v1/reviews/{review_id}/solution",
        headers=headers,
        json={"mode": "challenge"},
    )
    assert blocked.status_code == 403
    shown = client.post(
        f"/api/v1/reviews/{review_id}/solution",
        headers=headers,
        json={"mode": "guided"},
    )
    assert shown.status_code == 200
    assert shown.json()["revealed_choice"] == "b"
    helped = client.post(
        f"/api/v1/reviews/{review_id}/attempts",
        headers=headers,
        json={"choice": "b"},
    )
    assert helped.json()["assistance"] == "assisted"
    assert helped.json()["extended"] is False
    assert helped.json()["interval_days"] == 1
