"""S24: proposals fit seeded effort to real minutes and do not accept a plan."""

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import PlanVersion
from app.modules.learning.planner import (
    REASON_INSUFFICIENT,
    REASON_PREREQ,
    CompetencyWork,
    propose_plan,
)
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def test_greedy_scope_changes_with_usable_minutes() -> None:
    names = CompetencyWork("python.names", "Names", 10, 17, ())
    calls = CompetencyWork("python.calls", "Calls", 35, 65, ("python.names",))
    short = propose_plan([calls, names], 15)
    long = propose_plan([calls, names], 120)
    tiny = propose_plan([names, calls], 5)

    assert [item.key for item in short.included] == ["python.names"]
    assert short.deferred[0].key == "python.calls"
    assert short.deferred[0].reason_code == REASON_INSUFFICIENT
    assert short.estimated_required_low == 45
    assert short.scope_conflict is True

    assert [item.key for item in long.included] == ["python.names", "python.calls"]
    assert long.deferred == ()
    assert long.scope_conflict is False

    assert tiny.included == ()
    assert tiny.scope_conflict is True
    assert tiny.estimated_required_low > tiny.usable_minutes
    assert {item.reason_code for item in tiny.deferred} == {REASON_INSUFFICIENT, REASON_PREREQ}


def test_proposal_endpoint_does_not_create_a_plan_version() -> None:
    with SessionLocal() as db:
        seed(db)
        before = db.scalar(select(func.count()).select_from(PlanVersion))

    issued = client.post("/api/v1/dev/token", json={"email": "s24-planner@example.com"})
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}

    def goal(minutes: int) -> dict[str, object]:
        created = client.post(
            "/api/v1/goals",
            headers=headers,
            json={
                "title": "Learn Python",
                "domain_key": "python",
                "raw_request": "Names and function calls.",
                "time_budget": {
                    "mode": "one_off",
                    "one_off_minutes": minutes,
                    "preferred_session_minutes": 25,
                },
            },
        )
        assert created.status_code == 201
        proposed = client.post(
            f"/api/v1/goals/{created.json()['id']}/plan-proposals",
            headers=headers,
            json={},
        )
        assert proposed.status_code == 200
        return proposed.json()

    short = goal(15)
    long = goal(500)
    assert [item["competency_key"] for item in short["included"]] != [
        item["competency_key"] for item in long["included"]
    ]
    assert short["scope_conflict"] is True
    assert short["estimated_required_low"] > short["usable_minutes"]
    assert long["scope_conflict"] is False
    assert "python.calls" in [item["competency_key"] for item in long["included"]]

    with SessionLocal() as db:
        after = db.scalar(select(func.count()).select_from(PlanVersion))
    assert after == before
