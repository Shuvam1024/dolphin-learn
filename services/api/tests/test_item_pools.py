"""S62: unseen item pools; provisional graded items never selected for grading."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.main import app
from app.modules.curriculum.models import Competency
from app.modules.identity.models import User
from app.modules.learning.item_pool import pick_unseen
from app.modules.learning.models import (
    ActivityVersion,
    Attempt,
    CompetencyEvidence,
    Lesson,
    ReviewItem,
)
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


def _python_names_session(headers: dict[str, str]) -> tuple[str, list[dict[str, object]]]:
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
    names_questions = [
        item
        for item in accepted.json()["activities"]
        if item["title"].startswith("Names point at values:")
        and item["title"].endswith("objective")
    ]
    assert len(names_questions) >= 3
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    return started.json()["id"], names_questions


def _go_to(headers: dict[str, str], session_id: str, plan_activity_id: str, key: str) -> None:
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": key,
                "event_type": "progress",
                "payload": {"plan_activity_id": plan_activity_id},
            }
        },
    )


def test_fresh_check_avoids_seen_item_then_marks_repeat() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _auth("s62-pool")
    session_id, questions = _python_names_session(headers)
    first = questions[0]
    _go_to(headers, session_id, str(first["id"]), "to-a")
    client.post(
        f"/api/v1/sessions/{session_id}/solution",
        headers=headers,
        json={"mode": "guided"},
    )
    assisted = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "helped-a", "choice": "b"},
    )
    assert assisted.status_code == 200
    assert assisted.json()["eligible_for_independent_evidence"] is False

    seen_plan_ids = {str(first["id"])}
    for index in range(len(questions) - 1):
        moved = client.post(f"/api/v1/sessions/{session_id}/independent-check", headers=headers)
        assert moved.status_code == 200
        nxt = moved.json()["plan_activity_id"]
        assert str(nxt) not in seen_plan_ids
        seen_plan_ids.add(str(nxt))
        studio = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
        assert studio["studio_activity"]["state"]["repeat"] is False
        client.post(
            f"/api/v1/sessions/{session_id}/attempts",
            headers=headers,
            json={"idempotency_key": f"try-{index}-a", "choice": "a"},
        )
        client.post(
            f"/api/v1/sessions/{session_id}/attempts",
            headers=headers,
            json={"idempotency_key": f"try-{index}-b", "choice": "b"},
        )

    last = client.post(f"/api/v1/sessions/{session_id}/independent-check", headers=headers)
    assert last.status_code == 200
    studio = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert studio["studio_activity"]["state"]["repeat"] is True


def test_provisional_graded_items_never_returned_for_grading() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _auth("s62-prov")
    me = client.get("/api/v1/me", headers=headers).json()
    with SessionLocal() as db:
        competency = db.scalar(select(Competency).where(Competency.key == "python.names"))
        assert competency is not None
        lesson = db.scalar(select(Lesson).where(Lesson.competency_id == competency.id))
        assert lesson is not None
        max_version = db.scalar(
            select(ActivityVersion.version)
            .where(ActivityVersion.lesson_id == lesson.id)
            .order_by(ActivityVersion.version.desc())
        )
        provisional = ActivityVersion(
            lesson_id=lesson.id,
            version=(max_version or 0) + 1,
            item_id=f"provisional-obj-{uuid.uuid4().hex[:6]}",
            activity_type="objective",
            prompt="Provisional draft — must never grade.",
            answer_key={"correct": "a"},
            explanation="Draft only.",
            misconceptions={"b": "Draft note."},
            payload={"choices": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}]},
            provisional=True,
            source="ai",
            reviewed_at=None,
            effort_minutes_low=1,
            effort_minutes_high=2,
        )
        db.add(provisional)
        db.commit()
        provisional_id = provisional.id
        user = db.get(User, uuid.UUID(me["id"]))
        assert user is not None
        for _ in range(5):
            picked = pick_unseen(db, user, competency.id, graded=True)
            assert picked is not None
            assert picked.activity.id != provisional_id
            assert picked.activity.provisional is False


def test_reviews_rotate_across_pool() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _auth("s62-review")
    session_id, questions = _python_names_session(headers)
    _go_to(headers, session_id, str(questions[0]["id"]), "to-first")
    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "independent-first", "choice": "b"},
    )
    me = client.get("/api/v1/me", headers=headers)
    user_id = uuid.UUID(me.json()["id"])
    with SessionLocal() as db:
        item = db.scalar(select(ReviewItem).where(ReviewItem.user_id == user_id))
        assert item is not None
        item.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
        review_id = str(item.id)
        db.commit()

    first = client.get("/api/v1/reviews/due", headers=headers).json()["due"][0]
    assert first["prompt"]
    client.post(
        f"/api/v1/reviews/{review_id}/attempts",
        headers=headers,
        json={"choice": "a"},
    )
    with SessionLocal() as db:
        item = db.get(ReviewItem, uuid.UUID(review_id))
        assert item is not None
        item.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()
    second = client.get("/api/v1/reviews/due", headers=headers).json()["due"][0]
    assert second["prompt"] != first["prompt"]


def test_revealed_item_correct_stays_practicing_across_sessions() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _auth("s62-reveal")
    session_id, questions = _python_names_session(headers)
    goal = client.get("/api/v1/home", headers=headers).json()["goals"][0]
    _go_to(headers, session_id, str(questions[0]["id"]), "to-a")
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
    client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers)

    # New session: answer the same revealed item correctly with no help.
    started = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"goal_id": goal["id"]},
    )
    new_id = started.json()["id"]
    _go_to(headers, new_id, str(questions[0]["id"]), "to-a-again")
    correct = client.post(
        f"/api/v1/sessions/{new_id}/attempts",
        headers=headers,
        json={"idempotency_key": "after-reveal", "choice": "b"},
    )
    assert correct.status_code == 200
    assert correct.json()["assistance"] == "independent"
    assert correct.json()["eligible_for_independent_evidence"] is True
    with SessionLocal() as db:
        attempt_row = db.scalar(
            select(Attempt).where(Attempt.idempotency_key == "after-reveal")
        )
        assert attempt_row is not None
        facet = db.scalar(
            select(CompetencyEvidence.status_facet).where(
                CompetencyEvidence.attempt_id == attempt_row.id
            )
        )
    assert facet == "practicing"


def test_independent_check_ownership_404() -> None:
    with SessionLocal() as db:
        seed(db)
    owner = _auth("s62-owner")
    other = _auth("s62-other")
    session_id, questions = _python_names_session(owner)
    _go_to(owner, session_id, str(questions[0]["id"]), "to-a")
    denied = client.post(f"/api/v1/sessions/{session_id}/independent-check", headers=other)
    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "not_found"
