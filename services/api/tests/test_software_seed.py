"""S49: software domain plans its own competencies on the shared ledger."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.curriculum.models import Domain
from app.modules.learning.models import ActivityVersion, Lesson
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def test_software_domain_plans_only_software() -> None:
    with SessionLocal() as db:
        seed(db)
        seed(db)
        assert db.scalar(select(Domain).where(Domain.key == "software"))
        lesson = db.scalar(select(Lesson).where(Lesson.key == "software.failing_test.intro"))
        assert lesson is not None
        keyed = db.scalar(
            select(func.count())
            .select_from(ActivityVersion)
            .where(
                ActivityVersion.lesson_id == lesson.id,
                ActivityVersion.answer_key.is_not(None),
            )
        )
        assert keyed is not None and keyed >= 1

    listed = client.get("/api/v1/domains")
    assert listed.status_code == 200
    assert "software" in {item["key"] for item in listed.json()}

    headers = {
        "Authorization": (
            "Bearer "
            + client.post(
                "/api/v1/dev/token",
                json={"email": f"s49-{uuid.uuid4().hex[:8]}@example.com"},
            ).json()["access_token"]
        )
    }
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Read failing tests",
            "domain_key": "software",
            "raw_request": "Learn to read what a test expected.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 60,
                "preferred_session_minutes": 25,
            },
        },
    )
    assert created.status_code == 201
    assert created.json()["domain_key"] == "software"
    proposal = client.post(
        f"/api/v1/goals/{created.json()['id']}/plan-proposals",
        headers=headers,
        json={},
    )
    assert proposal.status_code == 200
    included = [item["competency_key"] for item in proposal.json()["included"]]
    assert included
    assert all(key.startswith("software.") for key in included)
    assert not any(key.startswith("python.") for key in included)
    assert not any(key.startswith("math.") for key in included)

    accepted = client.post(
        f"/api/v1/goals/{created.json()['id']}/plans/accept",
        headers=headers,
    )
    assert accepted.status_code == 201
    questions = [
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    ]
    started = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"goal_id": created.json()["id"]},
    )
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
    attempt = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "soft-1", "choice": "a"},
    )
    assert attempt.status_code == 200
    assert attempt.json()["outcome"] == "correct"
    assert attempt.json()["assistance"] == "independent"
