"""S30: assisted success is not independent demonstration; an unseen item can be."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import CompetencyEvidence
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


def test_assisted_success_does_not_demonstrate_and_unseen_item_does() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s30-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
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
    assert len(questions) >= 2
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "to-first-question",
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
    assisted = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "helped", "choice": "b"},
    )
    assert assisted.json()["eligible_for_independent_evidence"] is False

    progress = client.get("/api/v1/progress", headers=headers)
    assert progress.status_code == 200
    facets = {item["status_facet"] for item in progress.json()["facets"]}
    assert "independently_demonstrated" not in facets
    assert "retained" not in facets
    assert "applied" not in facets
    assert "practicing" in facets

    moved = client.post(f"/api/v1/sessions/{session_id}/independent-check", headers=headers)
    assert moved.status_code == 200
    assert moved.json()["activity"]["activity_type"] == "objective"
    assert moved.json()["plan_activity_id"] != questions[0]["id"]
    assert moved.json()["activity"]["revealed_choice"] == ""

    fresh = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "unseen", "choice": "a"},
    )
    # The second names question's key is "a" (rebind). Calls question key is "b".
    # Accept whichever the mover picked by reading eligibility, then assert the ledger.
    assert fresh.status_code == 200
    if not fresh.json()["eligible_for_independent_evidence"]:
        answer = "b" if fresh.json()["choice"] == "a" else "a"
        fresh = client.post(
            f"/api/v1/sessions/{session_id}/attempts",
            headers=headers,
            json={"idempotency_key": "unseen-retry", "choice": answer},
        )
    assert fresh.json()["assistance"] == "independent"
    assert fresh.json()["eligible_for_independent_evidence"] is True

    again = client.get("/api/v1/progress", headers=headers)
    shown = {item["status_facet"] for item in again.json()["facets"]}
    assert "independently_demonstrated" in shown
    assert "retained" not in shown
    assert "applied" not in shown

    me = client.get("/api/v1/me", headers=headers)
    with SessionLocal() as db:
        stored = set(
            db.scalars(
                select(CompetencyEvidence.status_facet).where(
                    CompetencyEvidence.user_id == me.json()["id"]
                )
            )
        )
    assert "retained" not in stored
    assert "applied" not in stored
