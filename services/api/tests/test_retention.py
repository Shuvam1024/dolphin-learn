"""S41: retained comes only from an independent review that was already due."""

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import ActivityVersion, ReviewItem
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


def _correct_for_prompt(prompt: str) -> str:
    with SessionLocal() as db:
        activity = db.scalar(select(ActivityVersion).where(ActivityVersion.prompt == prompt))
        assert activity is not None and activity.answer_key is not None
        return str(activity.answer_key.get("correct", ""))


def _due_choice(headers: dict[str, str]) -> str:
    due = client.get("/api/v1/reviews/due", headers=headers).json()["due"][0]
    return _correct_for_prompt(str(due["prompt"]))


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _session(headers: dict[str, str]) -> tuple[str, list[dict[str, str]]]:
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


def _facet(headers: dict[str, str]) -> str | None:
    progress = client.get("/api/v1/progress", headers=headers)
    for item in progress.json()["facets"]:
        if item["competency_key"] == "python.names":
            return str(item["status_facet"])
    return None


def _review_id(headers: dict[str, str]) -> uuid.UUID:
    me = client.get("/api/v1/me", headers=headers)
    user_id = uuid.UUID(me.json()["id"])
    with SessionLocal() as db:
        item = db.scalar(select(ReviewItem).where(ReviewItem.user_id == user_id))
        assert item is not None
        return item.id


def test_same_session_success_is_not_retained() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s41-session")
    session_id, questions = _session(headers)
    _answer(headers, session_id, questions[0]["id"], "once", "b")
    assert _facet(headers) == "independently_demonstrated"


def test_due_independent_review_sets_retained() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s41-due")
    session_id, questions = _session(headers)
    _answer(headers, session_id, questions[0]["id"], "once", "b")
    review_id = _review_id(headers)
    with SessionLocal() as db:
        item = db.get(ReviewItem, review_id)
        assert item is not None
        item.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()
    choice = _due_choice(headers)
    done = client.post(
        f"/api/v1/reviews/{review_id}/attempts",
        headers=headers,
        json={"choice": choice},
    )
    assert done.status_code == 200
    assert done.json()["retained"] is True
    assert done.json()["extended"] is True
    assert _facet(headers) == "retained"
    home = client.get("/api/v1/home", headers=headers)
    assert home.json()["recent_evidence"] == [
        {
            "competency_key": "python.names",
            "competency_name": "Names and values",
            "facet": "retained",
            "status_facet": "retained",
            "facet_label": "Remembered later",
        }
    ]
    assert "%" not in home.text
    assert "mastered" not in home.text


def test_early_or_assisted_review_does_not_retain() -> None:
    with SessionLocal() as db:
        seed(db)
    early = _headers("s41-early")
    session_id, questions = _session(early)
    _answer(early, session_id, questions[0]["id"], "once", "b")
    review_id = _review_id(early)
    due = client.get("/api/v1/reviews/due", headers=early).json()
    # Not due yet — still answer against the scheduled prompt's key.
    scheduled = due["scheduled"][0]
    soon = client.post(
        f"/api/v1/reviews/{review_id}/attempts",
        headers=early,
        json={"choice": _correct_for_prompt(str(scheduled["prompt"]))},
    )
    assert soon.json()["extended"] is True
    assert soon.json()["retained"] is False
    assert _facet(early) == "independently_demonstrated"

    helped = _headers("s41-helped")
    session_id, questions = _session(helped)
    _answer(helped, session_id, questions[0]["id"], "once", "b")
    review_id = _review_id(helped)
    with SessionLocal() as db:
        item = db.get(ReviewItem, review_id)
        assert item is not None
        item.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()
    shown = client.post(
        f"/api/v1/reviews/{review_id}/solution",
        headers=helped,
        json={"mode": "guided"},
    )
    assert shown.status_code == 200
    choice = shown.json()["revealed_choice"]
    assisted = client.post(
        f"/api/v1/reviews/{review_id}/attempts",
        headers=helped,
        json={"choice": choice},
    )
    assert assisted.json()["assistance"] == "assisted"
    assert assisted.json()["retained"] is False
    assert _facet(helped) == "independently_demonstrated"
