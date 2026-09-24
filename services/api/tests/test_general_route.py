"""S81: General route — learner-owned competencies for any subject."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.curriculum.models import Competency
from app.modules.learning.models import CompetencyState, Lesson, ReviewItem
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


def test_general_route_spanish_to_scheduled_recall() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s81")
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Spanish greetings",
            "domain_key": "general",
            "raw_request": "I want to greet people in Spanish.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 60,
                "preferred_session_minutes": 20,
            },
            "general": {
                "topic": "Spanish greetings",
                "outcomes": [
                    {"statement": "I can say hello and goodbye", "minutes": 15},
                    {"statement": "I can ask how someone is", "minutes": 15},
                ],
                "notes_markdown": "Hola means hello. Adiós means goodbye.",
            },
        },
    )
    assert created.status_code == 201, created.text
    goal_id = created.json()["id"]
    proposed = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers)
    assert proposed.status_code == 200
    assert len(proposed.json()["included"]) >= 1
    assert all(
        item["competency_key"].startswith("general.") for item in proposed.json()["included"]
    )
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    assert accepted.status_code == 201
    activities = accepted.json()["activities"]
    recall = next(item for item in activities if item["title"].endswith("free_recall"))

    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "to-recall",
                "event_type": "progress",
                "payload": {"plan_activity_id": recall["id"]},
            }
        },
    )
    attempt = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "recall-1", "text": "Hola means hello. Adiós means goodbye."},
    )
    assert attempt.status_code == 200, attempt.text
    rating = client.post(
        f"/api/v1/sessions/{session_id}/self-rate",
        headers=headers,
        json={"rating": "got_it"},
    )
    assert rating.status_code == 200, rating.text
    assert rating.json()["facet"] == "practicing"

    me = client.get("/api/v1/me", headers=headers)
    user_id = uuid.UUID(me.json()["id"])
    with SessionLocal() as db:
        review = db.scalar(select(ReviewItem).where(ReviewItem.user_id == user_id))
        assert review is not None
        competency = db.get(Competency, review.competency_id)
        assert competency is not None
        assert competency.owner_user_id == user_id
        assert competency.key.startswith("general.")
        state = db.get(CompetencyState, (user_id, competency.id))
        assert state is not None
        assert state.status_facet in {"practicing", "exposed"}
        assert state.status_facet != "independently_demonstrated"


def test_general_route_owner_isolation_and_limits() -> None:
    with SessionLocal() as db:
        seed(db)
    owner = _headers("s81-own")
    created = client.post(
        "/api/v1/goals",
        headers=owner,
        json={
            "title": "Spanish",
            "domain_key": "general",
            "raw_request": "Greetings",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 30,
                "preferred_session_minutes": 15,
            },
            "general": {
                "topic": "Spanish",
                "outcomes": [{"statement": "I can say hello", "minutes": 10}],
            },
        },
    )
    goal_id = created.json()["id"]
    other = _headers("s81-other")
    assert client.get(f"/api/v1/goals/{goal_id}", headers=other).status_code == 404
    assert (
        client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=other).status_code == 404
    )

    huge = client.post(
        "/api/v1/goals",
        headers=owner,
        json={
            "title": "Too much",
            "domain_key": "general",
            "raw_request": "notes",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 30,
                "preferred_session_minutes": 15,
            },
            "general": {
                "topic": "X",
                "outcomes": [{"statement": "I can try", "minutes": 10}],
                "notes_markdown": "x" * 20_001,
            },
        },
    )
    assert huge.status_code == 413

    html = client.post(
        "/api/v1/goals",
        headers=owner,
        json={
            "title": "Safe notes",
            "domain_key": "general",
            "raw_request": "notes",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 30,
                "preferred_session_minutes": 15,
            },
            "general": {
                "topic": "Safe",
                "outcomes": [{"statement": "I can stay safe", "minutes": 10}],
                "notes_markdown": "<script>alert(1)</script>Hello",
            },
        },
    )
    assert html.status_code == 201
    with SessionLocal() as db:
        lesson = db.scalar(
            select(Lesson)
            .join(Competency, Lesson.competency_id == Competency.id)
            .where(Competency.goal_id == uuid.UUID(html.json()["id"]))
        )
        assert lesson is not None
        assert "<script>" not in lesson.body_markdown
        assert "Hello" in lesson.body_markdown

    packed = client.post(
        "/api/v1/goals",
        headers=owner,
        json={
            "title": "Busy",
            "domain_key": "general",
            "raw_request": "many",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 60,
                "preferred_session_minutes": 20,
            },
            "general": {
                "topic": "Busy topic",
                "outcomes": [
                    {"statement": f"I can do outcome {i}", "minutes": 20} for i in range(1, 6)
                ],
            },
        },
    )
    assert packed.status_code == 201
    proposal = client.post(
        f"/api/v1/goals/{packed.json()['id']}/plan-proposals", headers=owner
    )
    assert proposal.status_code == 200
    deferred = proposal.json()["deferred"]
    assert deferred
    for item in deferred:
        assert item["reason_text"]
        assert "insufficient_minutes" not in item["reason_text"]


def test_general_missing_payload_rejected() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s81-miss")
    missing = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "No outcomes",
            "domain_key": "general",
            "raw_request": "oops",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 30,
                "preferred_session_minutes": 15,
            },
        },
    )
    assert missing.status_code == 422
