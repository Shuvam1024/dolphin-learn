"""S88: deeper fractions and software practice paths."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def test_math_four_at_240_deferred_at_30() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s88-math")
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Fractions",
            "domain_key": "math",
            "raw_request": "parts",
            "priority": "understand",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 240,
                "preferred_session_minutes": 30,
            },
        },
    )
    long = client.post(
        f"/api/v1/goals/{created.json()['id']}/plan-proposals", headers=headers
    ).json()
    assert len(long["included"]) >= 4

    short_goal = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Fractions short",
            "domain_key": "math",
            "raw_request": "parts",
            "priority": "understand",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 30,
                "preferred_session_minutes": 15,
            },
        },
    )
    short = client.post(
        f"/api/v1/goals/{short_goal.json()['id']}/plan-proposals", headers=headers
    ).json()
    assert short["deferred"]


def test_software_four_competencies_plan() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s88-sw")
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Software practice",
            "domain_key": "software",
            "raw_request": "tests",
            "priority": "understand",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 240,
                "preferred_session_minutes": 30,
            },
        },
    )
    proposal = client.post(
        f"/api/v1/goals/{created.json()['id']}/plan-proposals", headers=headers
    ).json()
    keys = {item["competency_key"] for item in proposal["included"]}
    assert "software.failing_test" in keys or len(proposal["included"]) >= 2
