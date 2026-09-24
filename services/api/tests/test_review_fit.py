"""S78: reviews estimate minutes and what fits this sitting."""

import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import ReviewItem
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)

_FORBIDDEN = re.compile(r"\b(overdue|missed|streak)\b", re.I)


def _due_review(headers: dict[str, str], *, preferred: int = 25) -> str:
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
                "preferred_session_minutes": preferred,
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
        return str(item.id)


def test_review_fit_estimates_and_forbidden_words() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s78-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    _due_review(headers, preferred=25)
    due = client.get("/api/v1/reviews/due", headers=headers)
    assert due.status_code == 200
    body = due.json()
    assert len(body["due"]) >= 1
    assert body["due"][0]["estimated_minutes"] >= 1
    assert body["preferred_session_minutes"] == 25
    assert body["fits"]["count"] >= 1
    assert body["fits"]["minutes"] >= body["due"][0]["estimated_minutes"]
    assert _FORBIDDEN.search(due.text) is None
    for item in body["due"] + body["scheduled"]:
        assert _FORBIDDEN.search(item["reason"]) is None


def test_snooze_presets_3_24_72() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s78-snooze-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    review_id = _due_review(headers)
    for hours in (3, 24, 72):
        # Re-due the item before each snooze check after the first
        if hours != 3:
            with SessionLocal() as db:
                item = db.get(ReviewItem, uuid.UUID(review_id))
                assert item is not None
                item.due_at = datetime.now(timezone.utc) - timedelta(minutes=5)
                db.commit()
        snoozed = client.post(
            f"/api/v1/reviews/{review_id}/snooze",
            headers=headers,
            json={"hours": hours},
        )
        assert snoozed.status_code == 200
        assert snoozed.json()["hours"] == hours
        assert snoozed.json()["unchanged_interval"] is True


def test_review_module_avoids_forbidden_words() -> None:
    root = Path(__file__).resolve().parents[1] / "app" / "modules" / "learning"
    text = (root / "reviews.py").read_text() + (root / "review_router.py").read_text()
    assert _FORBIDDEN.search(text) is None
