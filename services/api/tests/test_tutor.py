"""S63: explain differently and validated hints with seeded fallback."""

from __future__ import annotations

import uuid

import pytest
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.modules.ai_gateway.service import get_fake_provider, reset_provider
from app.modules.learning.models import ActivityVersion
from app.modules.learning.tutor import SEEDED_HINT, hint_validator
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def _ai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(settings, "ai_provider", "fake")
    monkeypatch.setattr(settings, "ai_daily_cap", 50)
    monkeypatch.setattr(settings, "ai_timeout_s", 12.0)
    reset_provider()
    fake = get_fake_provider()
    fake.scripts.clear()
    fake.calls.clear()
    fake.delay_s = 0.0
    yield
    reset_provider()


def _auth(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _session_on_objective(headers: dict[str, str]) -> str:
    with SessionLocal() as db:
        seed(db)
    created = client.post(
        "/api/v1/goals",
        headers=headers,
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
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    questions = [
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    ]
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "to-q",
                "event_type": "progress",
                "payload": {"plan_activity_id": questions[0]["id"]},
            }
        },
    )
    return session_id


def test_hint_validator_rejects_answer_leak() -> None:
    activity = ActivityVersion(
        lesson_id=uuid.uuid4(),
        version=1,
        item_id="t1",
        activity_type="objective",
        prompt="q",
        answer_key={"correct": "b"},
        payload={
            "choices": [
                {"id": "a", "label": "Wrong"},
                {"id": "b", "label": "The name is bound to the value"},
            ]
        },
        effort_minutes_low=1,
        effort_minutes_high=2,
    )
    assert hint_validator(activity, "Look at how assignment works.") is True
    assert hint_validator(activity, "the answer is b") is False
    assert hint_validator(activity, "Pick b carefully") is False
    assert hint_validator(activity, "The name is bound to the value") is False


def test_leaky_hint_falls_back_to_seeded() -> None:
    headers = _auth("s63-leak")
    session_id = _session_on_objective(headers)
    fake = get_fake_provider()
    fake.script("hint", {"hint": "the answer is b"})
    helped = client.post(
        f"/api/v1/sessions/{session_id}/hint",
        headers=headers,
        json={"mode": "guided"},
    )
    assert helped.status_code == 200
    assert helped.json()["message"] == SEEDED_HINT
    assert helped.json()["hint_source"] == "seed"
    studio = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert studio["studio_activity"]["state"]["hint_text"] == SEEDED_HINT
    assert studio["studio_activity"]["state"]["hint_source"] == "seed"
    attempt = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "after-hint", "choice": "b"},
    )
    assert attempt.json()["assistance"] == "assisted"


def test_ai_hint_accepted_when_clean() -> None:
    headers = _auth("s63-clean")
    session_id = _session_on_objective(headers)
    fake = get_fake_provider()
    fake.script("hint", {"hint": "Think about what assignment does to a name."})
    helped = client.post(
        f"/api/v1/sessions/{session_id}/hint",
        headers=headers,
        json={"mode": "guided"},
    )
    assert helped.status_code == 200
    assert helped.json()["hint_source"] == "ai"
    assert "assignment" in helped.json()["message"]


def test_explain_records_help_and_increases_count() -> None:
    headers = _auth("s63-explain")
    session_id = _session_on_objective(headers)
    fake = get_fake_provider()
    fake.script(
        "explain_differently",
        {
            "explanation_markdown": "A name is a label stuck on a value.",
            "analogy_used": True,
        },
    )
    before = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert before["tutor"]["enabled"] is True
    explained = client.post(f"/api/v1/sessions/{session_id}/explain", headers=headers)
    assert explained.status_code == 200
    assert explained.json()["hint_count"] >= 1
    assert "label" in explained.json()["explanation_markdown"]
    studio = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert studio["studio_activity"]["state"]["alt_explanation"]
    attempt = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "after-explain", "choice": "b"},
    )
    assert attempt.json()["assistance"] == "assisted"


def test_explain_404_when_ai_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", False)
    monkeypatch.setattr(settings, "ai_provider", "")
    reset_provider()
    headers = _auth("s63-off")
    session_id = _session_on_objective(headers)
    denied = client.post(f"/api/v1/sessions/{session_id}/explain", headers=headers)
    assert denied.status_code == 404
    studio = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert studio["tutor"]["enabled"] is False
    # Seeded hint still works with AI off.
    helped = client.post(
        f"/api/v1/sessions/{session_id}/hint",
        headers=headers,
        json={"mode": "guided"},
    )
    assert helped.status_code == 200
    assert helped.json()["hint_source"] == "seed"
    assert helped.json()["message"] == SEEDED_HINT
