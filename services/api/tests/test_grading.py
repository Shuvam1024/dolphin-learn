"""S29: unassisted correct work is eligible; a revealed solution marks the next attempt assisted."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.learning.grading import eligible_for_independent_evidence, grade_choice
from app.modules.learning.models import CompetencyEvidence
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


def test_grade_choice_matches_the_versioned_key() -> None:
    outcome, score = grade_choice({"correct": "b"}, "b")
    assert outcome == "correct"
    assert score == 1
    wrong, zero = grade_choice({"correct": "b"}, "a")
    assert wrong == "incorrect"
    assert zero == 0
    assert eligible_for_independent_evidence("independent", "correct") is True
    assert eligible_for_independent_evidence("assisted", "correct") is False


def _question_session() -> tuple[dict[str, str], str]:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s29-{uuid.uuid4().hex[:8]}@example.com"},
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
                "client_event_id": "to-question",
                "event_type": "progress",
                "payload": {"plan_activity_id": question["id"]},
            }
        },
    )
    return headers, session_id


def test_unassisted_correct_is_eligible_and_solution_marks_assisted() -> None:
    headers, session_id = _question_session()
    hidden = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert hidden.json()["activity"]["revealed_choice"] == ""
    assert "answer_key" not in hidden.text

    blocked = client.post(
        f"/api/v1/sessions/{session_id}/solution",
        headers=headers,
        json={"mode": "challenge"},
    )
    assert blocked.status_code == 403
    still_hidden = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert still_hidden.json()["activity"]["revealed_choice"] == ""

    correct = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "plain", "choice": "b"},
    )
    assert correct.status_code == 200
    assert correct.json()["assistance"] == "independent"
    assert correct.json()["outcome"] == "correct"
    assert correct.json()["eligible_for_independent_evidence"] is True

    hint = client.post(f"/api/v1/sessions/{session_id}/hint", headers=headers, json={})
    assert hint.status_code == 200
    assert hint.json()["revealed_choice"] == ""
    assert "letter" in hint.json()["message"]

    solution = client.post(
        f"/api/v1/sessions/{session_id}/solution",
        headers=headers,
        json={"mode": "guided"},
    )
    assert solution.status_code == 200
    assert solution.json()["revealed_choice"] == "b"

    assisted = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "after-solution", "choice": "b"},
    )
    assert assisted.json()["assistance"] == "assisted"
    assert assisted.json()["outcome"] == "correct"
    assert assisted.json()["eligible_for_independent_evidence"] is False

    me = client.get("/api/v1/me", headers=headers)
    with SessionLocal() as db:
        facets = set(
            db.scalars(
                select(CompetencyEvidence.status_facet).where(
                    CompetencyEvidence.user_id == me.json()["id"]
                )
            )
        )
    assert "retained" not in facets
    assert "applied" not in facets
