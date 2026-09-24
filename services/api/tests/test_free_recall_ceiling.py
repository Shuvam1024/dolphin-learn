"""S65: free recall self-report never exceeds practicing."""

from __future__ import annotations

import uuid

import pytest
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.modules.ai_gateway.service import get_fake_provider, reset_provider
from app.modules.learning.models import CompetencyEvidence, CompetencyState
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


@pytest.fixture(autouse=True)
def _ai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(settings, "ai_provider", "fake")
    reset_provider()
    fake = get_fake_provider()
    fake.scripts.clear()
    fake.calls.clear()
    yield
    reset_provider()


def _auth(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _on_recall(headers: dict[str, str]) -> str:
    with SessionLocal() as db:
        seed(db)
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 180,
                "preferred_session_minutes": 30,
            },
        },
    )
    goal_id = created.json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    recalls = [
        item
        for item in accepted.json()["activities"]
        if item["title"].endswith("free_recall")
    ]
    assert recalls
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "to-recall",
                "event_type": "progress",
                "payload": {"plan_activity_id": recalls[0]["id"]},
            }
        },
    )
    return session_id


def test_free_recall_ceiling_and_self_reported() -> None:
    headers = _auth("s65-ceil")
    session_id = _on_recall(headers)
    before = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert before["studio_activity"]["body_markdown"] == ""
    written = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "recall-1", "text": "A name points at a value."},
    )
    assert written.status_code == 200
    after = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert after["studio_activity"]["body_markdown"]
    assert after["studio_activity"]["state"]["awaiting_self_report"] is True
    assert after["studio_activity"]["state"]["recall_feedback"]
    rated = client.post(
        f"/api/v1/sessions/{session_id}/self-rate",
        headers=headers,
        json={"rating": "got_it"},
    )
    assert rated.status_code == 200
    assert rated.json()["facet"] == "practicing"
    me = client.get("/api/v1/me", headers=headers).json()
    with SessionLocal() as db:
        facets = set(
            db.scalars(
                select(CompetencyEvidence.status_facet).where(
                    CompetencyEvidence.user_id == me["id"]
                )
            )
        )
        state = db.scalar(
            select(CompetencyState).where(CompetencyState.user_id == me["id"])
        )
    assert facets <= {"exposed", "practicing"}
    assert "independently_demonstrated" not in facets
    assert "retained" not in facets
    assert state is not None
    assert state.status_facet == "practicing"
    done = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert done["studio_activity"]["state"]["outcome"] == "self_reported"


def test_ai_compare_cannot_change_rating_or_facet() -> None:
    headers = _auth("s65-ai")
    session_id = _on_recall(headers)
    fake = get_fake_provider()
    fake.script(
        "recall_compare",
        {
            "covered": ["everything"],
            "missing": [],
            "one_sentence_feedback": "Perfect mastery forever.",
        },
    )
    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "recall-ai", "text": "names"},
    )
    rated = client.post(
        f"/api/v1/sessions/{session_id}/self-rate",
        headers=headers,
        json={"rating": "not_yet"},
    )
    assert rated.json()["facet"] == "exposed"
    assert rated.json()["rating"] == "not_yet"
