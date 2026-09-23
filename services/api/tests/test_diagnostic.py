"""S23: a diagnostic can be skipped or answered without claiming mastery."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import Attempt, CompetencyEvidence
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def _headers(email: str) -> dict[str, str]:
    issued = client.post("/api/v1/dev/token", json={"email": email})
    assert issued.status_code == 200
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _goal(headers: dict[str, str]) -> str:
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Learn Python", "raw_request": "Bind names to values."},
    )
    assert created.status_code == 201
    return created.json()["id"]


def test_skip_or_answer_without_mastery_and_retry() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers(f"s23-{uuid.uuid4().hex[:8]}@example.com")
    goal_id = _goal(headers)

    started = client.post(
        f"/api/v1/goals/{goal_id}/diagnostic",
        headers=headers,
        json={"action": "start"},
    )
    assert started.status_code == 200
    body = started.json()
    assert body["mastery_claimed"] is False
    assert 3 <= len(body["items"]) <= 8
    assert "correct" not in started.text
    items = body["items"]

    partial = client.post(
        f"/api/v1/goals/{goal_id}/diagnostic",
        headers=headers,
        json={
            "action": "submit",
            "answers": [{"activity_version_id": items[0]["activity_version_id"], "choice": "b"}],
        },
    )
    assert partial.status_code == 200
    assert partial.json()["status"] == "recorded"
    assert partial.json()["mastery_claimed"] is False
    assert len(partial.json()["attempts"]) == 1

    rest = client.post(
        f"/api/v1/goals/{goal_id}/diagnostic",
        headers=headers,
        json={
            "action": "submit",
            "answers": [
                {"activity_version_id": item["activity_version_id"], "choice": "a"}
                for item in items[1:]
            ],
        },
    )
    assert rest.status_code == 200
    assert rest.json()["mastery_claimed"] is False

    skipped = client.post(
        f"/api/v1/goals/{goal_id}/diagnostic",
        headers=headers,
        json={"action": "skip"},
    )
    assert skipped.status_code == 200
    assert skipped.json()["status"] == "skipped"
    assert skipped.json()["mastery_claimed"] is False

    again = client.post(
        f"/api/v1/goals/{goal_id}/diagnostic",
        headers=headers,
        json={"action": "start"},
    )
    assert again.status_code == 200
    assert 3 <= len(again.json()["items"]) <= 8

    me = client.get("/api/v1/me", headers=headers)
    user_id = me.json()["id"]
    with SessionLocal() as db:
        evidence = db.scalar(
            select(func.count())
            .select_from(CompetencyEvidence)
            .where(CompetencyEvidence.user_id == user_id)
        )
        attempts = db.scalar(
            select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id)
        )
    assert evidence == 0
    assert attempts == len(items)


def test_other_user_cannot_start_diagnostic() -> None:
    owner = _headers("s23-owner@example.com")
    other = _headers("s23-other@example.com")
    goal_id = _goal(owner)
    hidden = client.post(
        f"/api/v1/goals/{goal_id}/diagnostic",
        headers=other,
        json={"action": "skip"},
    )
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "not_found"
