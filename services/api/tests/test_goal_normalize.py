"""S83: AI goal normalizer suggests title, subject, and outcomes."""

from __future__ import annotations

import uuid

import pytest
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.modules.ai_gateway.service import get_fake_provider, reset_provider
from app.modules.goals.models import Goal
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


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def test_goal_normalize_suggests_without_saving() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s83")
    before = list(
        SessionLocal().scalars(select(Goal)).all()
    )
    response = client.post(
        "/api/v1/goals/normalize",
        headers=headers,
        json={"text": "I want to learn Python variable names"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"]
    assert len(body["title"]) <= 60
    assert body["domain_key"] == "python"
    assert 1 <= len(body["outcomes"]) <= 5
    assert all(item.lower().startswith("i can") for item in body["outcomes"])
    assert body["minutes_hint_per_outcome"] >= 1
    assert 0 <= body["confidence"] <= 1
    assert body["source"] == "ai"
    after = list(SessionLocal().scalars(select(Goal)).all())
    assert len(after) == len(before)


def test_goal_normalize_rejects_unknown_domain() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s83-bad")
    fake = get_fake_provider()
    fake.script(
        "goal_normalize",
        {
            "title": "Alchemy",
            "domain_key": "alchemy",
            "outcomes": ["I can turn lead into gold"],
            "minutes_hint_per_outcome": 10,
            "confidence": 0.9,
        },
    )
    response = client.post(
        "/api/v1/goals/normalize",
        headers=headers,
        json={"text": "teach me alchemy"},
    )
    assert response.status_code == 422


def test_goal_normalize_degraded_when_ai_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", False)
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s83-off")
    response = client.post(
        "/api/v1/goals/normalize",
        headers=headers,
        json={"text": "learn python"},
    )
    assert response.status_code == 404
