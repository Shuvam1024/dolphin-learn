"""S46: snooze delays a review without awarding retention."""

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import CompetencyEvidence, ReviewEvent, ReviewItem
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _due_review(headers: dict[str, str]) -> uuid.UUID:
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
    with SessionLocal() as db:
        item = db.scalar(select(ReviewItem).where(ReviewItem.user_id == user_id))
        assert item is not None
        item.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()
        return item.id


def test_snooze_moves_due_time_without_retention_or_interval_change() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s46")
    review_id = _due_review(headers)
    me = client.get("/api/v1/me", headers=headers)
    user_id = uuid.UUID(me.json()["id"])
    with SessionLocal() as db:
        item = db.get(ReviewItem, review_id)
        assert item is not None
        before_due = item.due_at
        before_interval = item.interval_days
        evidence_before = int(
            db.scalar(
                select(func.count())
                .select_from(CompetencyEvidence)
                .where(CompetencyEvidence.user_id == user_id)
            )
            or 0
        )

    due = client.get("/api/v1/reviews/due", headers=headers)
    assert any(item["id"] == str(review_id) for item in due.json()["due"])

    snoozed = client.post(
        f"/api/v1/reviews/{review_id}/snooze",
        headers=headers,
        json={"hours": 24},
    )
    assert snoozed.status_code == 200
    body = snoozed.json()
    assert body["hours"] == 24
    assert body["retained"] is False
    assert body["extended"] is False
    assert body["unchanged_interval"] is True
    assert body["interval_days"] == before_interval

    with SessionLocal() as db:
        item = db.get(ReviewItem, review_id)
        assert item is not None
        assert item.interval_days == before_interval
        assert item.due_at > before_due
        assert item.due_at >= datetime.now(timezone.utc) + timedelta(hours=23)
        evidence_after = int(
            db.scalar(
                select(func.count())
                .select_from(CompetencyEvidence)
                .where(CompetencyEvidence.user_id == user_id)
            )
            or 0
        )
        assert evidence_after == evidence_before
        events = list(
            db.scalars(
                select(ReviewEvent).where(ReviewEvent.review_item_id == review_id)
            ).all()
        )
        assert any(event.outcome == "snooze" for event in events)
        retained_rows = db.scalars(
            select(CompetencyEvidence).where(
                CompetencyEvidence.user_id == user_id,
                CompetencyEvidence.status_facet == "retained",
            )
        ).all()
        assert retained_rows == []

    queue = client.get("/api/v1/reviews/due", headers=headers)
    assert all(item["id"] != str(review_id) for item in queue.json()["due"])
    assert any(item["id"] == str(review_id) for item in queue.json()["scheduled"])

    bad = client.post(
        f"/api/v1/reviews/{review_id}/snooze",
        headers=headers,
        json={"hours": 0},
    )
    assert bad.status_code == 422
    other = _headers("s46-other")
    denied = client.post(
        f"/api/v1/reviews/{review_id}/snooze",
        headers=other,
        json={"hours": 12},
    )
    assert denied.status_code == 404
