"""S39: another learner cannot read or write this learner's goal, session, or attempt."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import Attempt
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def test_cross_user_goal_session_and_attempt_are_not_found() -> None:
    with SessionLocal() as db:
        seed(db)
    owner = _headers("s39-owner")
    other = _headers("s39-other")
    created = client.post(
        "/api/v1/goals",
        headers=owner,
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
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=owner)
    question = next(
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    )
    started = client.post("/api/v1/sessions", headers=owner, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=owner,
        json={
            "event": {
                "client_event_id": "to-q",
                "event_type": "progress",
                "payload": {"plan_activity_id": question["id"]},
            }
        },
    )
    submitted = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=owner,
        json={"idempotency_key": "once", "choice": "b"},
    )
    assert submitted.status_code == 200
    attempt_id = submitted.json()["id"]

    denied = [
        client.get(f"/api/v1/goals/{goal_id}", headers=other),
        client.get(f"/api/v1/goals/{goal_id}/plan", headers=other),
        client.get(f"/api/v1/goals/{goal_id}/overview", headers=other),
        client.post(f"/api/v1/goals/{goal_id}/replan", headers=other),
        client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=other),
        client.get(f"/api/v1/sessions/{session_id}", headers=other),
        client.patch(
            f"/api/v1/sessions/{session_id}",
            headers=other,
            json={
                "event": {
                    "client_event_id": "stolen",
                    "event_type": "pause",
                    "payload": {},
                }
            },
        ),
        client.post(
            f"/api/v1/sessions/{session_id}/attempts",
            headers=other,
            json={"idempotency_key": "stolen", "choice": "a"},
        ),
        client.post(f"/api/v1/sessions/{session_id}/advance", headers=other),
        client.post(f"/api/v1/sessions/{session_id}/independent-check", headers=other),
        client.post(f"/api/v1/sessions/{session_id}/finish", headers=other),
    ]
    assert [item.status_code for item in denied] == [404] * len(denied)
    assert all(item.json()["error"]["code"] == "not_found" for item in denied)

    assert client.get("/api/v1/home", headers=other).json()["goals"] == []
    assert client.get("/api/v1/progress", headers=other).json()["facets"] == []
    assert client.get("/api/v1/reviews/due", headers=other).json()["scheduled"] == []

    owner_home = client.get("/api/v1/home", headers=owner).json()
    assert owner_home["goals"][0]["id"] == goal_id
    facets = client.get("/api/v1/progress", headers=owner).json()["facets"]
    demonstrated = {
        "competency_key": "python.names",
        "competency_name": "Names and values",
        "status_facet": "independently_demonstrated",
        "facet_label": "Shown on your own",
    }
    assert demonstrated in facets

    me = client.get("/api/v1/me", headers=owner)
    user_id = uuid.UUID(me.json()["id"])
    with SessionLocal() as db:
        count = db.scalar(
            select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id)
        )
    assert int(count or 0) == 1
    again = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=owner,
        json={"idempotency_key": "once", "choice": "a"},
    )
    assert again.json()["id"] == attempt_id
    assert again.json()["created"] is False
    assert again.json()["choice"] == "b"
