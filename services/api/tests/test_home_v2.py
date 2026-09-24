"""S72: Home v2 ranking — one next action, cards, due reviews, evidence chips."""

from __future__ import annotations

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


def test_home_v2_card_shape_and_ranking() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s72")
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 25,
            },
        },
    )
    goal_id = created.json()["id"]
    client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    home = client.get("/api/v1/home", headers=headers).json()
    action = home["next_action"]
    assert action["kind"] == "start_session"
    assert action["subtitle"]
    assert "minutes_estimate" in action
    assert action["href"].endswith("/start")
    card = home["goals"][0]
    assert card["subject_name"]
    assert card["next_lesson_title"]
    assert card["remaining_minutes"] == 120
    assert card["usable_minutes"] == 120
    assert card["studied_minutes"] == 0
    assert card["status"] == "active"
    assert home["due_reviews"]["count"] == 0
    assert isinstance(home["recent_evidence"], list)
    assert "streak" not in str(home).lower()
    assert "mastery" not in str(home).lower()
