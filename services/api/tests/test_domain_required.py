"""S47: goals require an explicit seeded domain; titles do not invent one."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _headers(email: str) -> dict[str, str]:
    issued = client.post("/api/v1/dev/token", json={"email": email})
    assert issued.status_code == 200
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def test_domains_list_and_cooking_is_not_python() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers(f"s47-{uuid.uuid4().hex[:8]}@example.com")

    listed = client.get("/api/v1/domains", headers=headers)
    assert listed.status_code == 200
    keys = {item["key"] for item in listed.json()}
    assert {"math", "python"} <= keys
    assert "cooking" not in keys

    missing = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn cooking",
            "raw_request": "I want to cook pasta.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 30,
            },
        },
    )
    assert missing.status_code == 422

    unknown = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn cooking",
            "raw_request": "I want to cook pasta.",
            "domain_key": "cooking",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 30,
            },
        },
    )
    assert unknown.status_code == 422
    assert "do not have lessons" in unknown.json()["error"]["message"]

    cooking_as_python_title = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn cooking",
            "raw_request": "I want to cook pasta.",
            "domain_key": "math",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 30,
                "preferred_session_minutes": 30,
            },
        },
    )
    assert cooking_as_python_title.status_code == 201
    goal_id = cooking_as_python_title.json()["id"]
    assert cooking_as_python_title.json()["domain_key"] == "math"

    proposal = client.post(
        f"/api/v1/goals/{goal_id}/plan-proposals",
        headers=headers,
        json={},
    )
    assert proposal.status_code == 200
    included = [item["competency_key"] for item in proposal.json()["included"]]
    assert all(key.startswith("math.") for key in included)
    assert not any(key.startswith("python.") for key in included)
