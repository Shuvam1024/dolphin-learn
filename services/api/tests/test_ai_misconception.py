"""S64: AI misconception notes cannot alter the grading outcome."""

from __future__ import annotations

import uuid

import pytest
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.modules.ai_gateway.service import get_fake_provider, reset_provider
from app.modules.learning.models import Evaluation
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


def _on_short(headers: dict[str, str]) -> str:
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
                "one_off_minutes": 120,
                "preferred_session_minutes": 25,
            },
        },
    )
    goal_id = created.json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    shorts = [
        item
        for item in accepted.json()["activities"]
        if item["title"].endswith("short_answer")
    ]
    assert shorts
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "to-short",
                "event_type": "progress",
                "payload": {"plan_activity_id": shorts[0]["id"]},
            }
        },
    )
    return session_id


def test_model_cannot_alter_outcome_and_rejects_answer_leak() -> None:
    headers = _auth("s64-note")
    session_id = _on_short(headers)
    fake = get_fake_provider()
    fake.script(
        "misconception_note",
        {"note": "The correct answer is binds the name to a value", "tag": "other"},
    )
    wrong = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "wrong-1", "text": "locks a permanent box"},
    )
    assert wrong.status_code == 200
    assert wrong.json()["outcome"] == "incorrect"
    assert wrong.json()["misconception_note"] == ""
    # Clean note on a fresh attempt key after clearing scripts to use default.
    fake.scripts.clear()
    fake.script(
        "misconception_note",
        {"note": "That treats a name like a locked box.", "tag": "other"},
    )
    # Need a new session activity attempt — use new idempotency after independent-check
    # is not available for short; re-submit is blocked by recorded state. Start over.
    session_id = _on_short(headers)
    fake.script(
        "misconception_note",
        {"note": "That treats a name like a locked box.", "tag": "other"},
    )
    noted = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "wrong-2", "text": "locks a permanent box"},
    )
    assert noted.json()["outcome"] == "incorrect"
    assert noted.json()["misconception_note"]
    assert noted.json()["misconception_source"] == "ai"
    with SessionLocal() as db:
        evaluation = db.scalar(
            select(Evaluation).where(Evaluation.attempt_id == noted.json()["id"])
        )
        assert evaluation is not None
        assert evaluation.outcome == "incorrect"
        assert evaluation.feedback_json is not None


def test_flag_off_skips_misconception_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", False)
    monkeypatch.setattr(settings, "ai_provider", "")
    reset_provider()
    headers = _auth("s64-off")
    session_id = _on_short(headers)
    fake = get_fake_provider()
    fake.calls.clear()
    wrong = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "wrong-off", "text": "locks a permanent box"},
    )
    assert wrong.status_code == 200
    assert wrong.json()["outcome"] == "incorrect"
    assert wrong.json()["misconception_note"] == ""
    assert "misconception_note" not in fake.calls
