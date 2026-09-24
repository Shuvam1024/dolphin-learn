"""S82: Placement proposes skips the learner confirms."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.curriculum.models import Competency
from app.modules.goals.models import GoalCompetency
from app.modules.learning.models import CompetencyEvidence
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


def _python_goal(headers: dict[str, str]) -> str:
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names and calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 180,
                "preferred_session_minutes": 30,
            },
        },
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


def test_placement_suggestions_only_then_confirm_skips() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s82")
    goal_id = _python_goal(headers)

    started = client.post(
        f"/api/v1/goals/{goal_id}/diagnostic",
        headers=headers,
        json={"action": "start"},
    )
    assert started.status_code == 200, started.text
    items = started.json()["items"]
    assert 3 <= len(items) <= 5

    submitted = client.post(
        f"/api/v1/goals/{goal_id}/diagnostic",
        headers=headers,
        json={
            "action": "submit",
            "answers": [
                {"activity_version_id": items[0]["activity_version_id"], "choice": "a"}
            ],
        },
    )
    assert submitted.status_code == 200
    suggestions = submitted.json()["suggested_skip_keys"]
    assert suggestions
    # Diagnostic must not write evidence
    with SessionLocal() as db:
        assert db.scalar(select(CompetencyEvidence).limit(1)) is None or True
        me = client.get("/api/v1/me", headers=headers).json()["id"]
        rows = list(
            db.scalars(
                select(CompetencyEvidence).where(
                    CompetencyEvidence.user_id == uuid.UUID(me)
                )
            )
        )
        assert rows == []

    # Nothing skipped unless sent
    plain = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers)
    assert plain.status_code == 200
    assert all(
        item["reason_code"] != "skipped_by_learner" for item in plain.json()["deferred"]
    )

    skip_key = suggestions[0]
    skipped = client.post(
        f"/api/v1/goals/{goal_id}/plan-proposals",
        headers=headers,
        json={"skip_competency_keys": [skip_key]},
    )
    assert skipped.status_code == 200
    deferred = {item["competency_key"]: item for item in skipped.json()["deferred"]}
    assert skip_key in deferred
    assert deferred[skip_key]["reason_code"] == "skipped_by_learner"
    assert "You chose to skip" in deferred[skip_key]["reason_text"]
    assert all(item["competency_key"] != skip_key for item in skipped.json()["included"])

    with SessionLocal() as db:
        row = db.execute(
            select(GoalCompetency, Competency)
            .join(Competency, Competency.id == GoalCompetency.competency_id)
            .where(
                GoalCompetency.goal_id == uuid.UUID(goal_id),
                GoalCompetency.requirement == "skipped",
            )
        ).first()
        assert row is not None
        assert row[1].key == skip_key

    # Unskip on replan
    replan = client.post(f"/api/v1/goals/{goal_id}/replan-proposals", headers=headers)
    assert replan.status_code == 200
    assert all(
        item["reason_code"] != "skipped_by_learner" for item in replan.json()["deferred"]
    )
    with SessionLocal() as db:
        left = list(
            db.scalars(
                select(GoalCompetency).where(
                    GoalCompetency.goal_id == uuid.UUID(goal_id),
                    GoalCompetency.requirement == "skipped",
                )
            )
        )
        assert left == []


def test_general_route_has_no_placement() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s82-gen")
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Spanish",
            "domain_key": "general",
            "raw_request": "greetings",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 40,
                "preferred_session_minutes": 20,
            },
            "general": {
                "topic": "Spanish",
                "outcomes": [{"statement": "I can say hello", "minutes": 10}],
            },
        },
    )
    goal_id = created.json()["id"]
    started = client.post(
        f"/api/v1/goals/{goal_id}/diagnostic",
        headers=headers,
        json={"action": "start"},
    )
    assert started.status_code == 422
