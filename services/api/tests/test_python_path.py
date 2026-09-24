"""S87: Python fundamentals path depth."""

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


def test_python_path_420_understand_covers_six() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s87-420")
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "fundamentals",
            "priority": "understand",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 420,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    proposal = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers)
    assert proposal.status_code == 200
    included = proposal.json()["included"]
    assert len(included) >= 6


def test_python_path_120_starts_with_basics() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s87-120")
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "start small",
            "priority": "understand",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    proposal = client.post(f"/api/v1/goals/{goal_id}/plan-proposals", headers=headers)
    keys = [item["competency_key"] for item in proposal.json()["included"]]
    assert "python.names" in keys
    assert "python.calls" in keys
    assert "python.conditionals" in keys
