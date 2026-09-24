"""S93: gateway timeout and daily-cap safety for every eval prompt."""

from __future__ import annotations

import uuid

import pytest
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.modules.ai_gateway.models import AiCall
from app.modules.ai_gateway.schemas import GatewayError
from app.modules.ai_gateway.service import complete, get_fake_provider, reset_provider
from app.modules.identity.models import User
from app.modules.identity.service import ensure_profile
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field
from tests.ai_eval import PROMPTS

client = TestClient(app)


class _TinyOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    note: str = Field(default="x", max_length=40)


@pytest.fixture(autouse=True)
def _ai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(settings, "ai_provider", "fake")
    monkeypatch.setattr(settings, "ai_daily_cap", 3)
    monkeypatch.setattr(settings, "ai_timeout_s", 0.2)
    reset_provider()
    fake = get_fake_provider()
    fake.scripts.clear()
    fake.calls.clear()
    fake.delay_s = 0.0
    yield
    reset_provider()


def _user() -> User:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s93-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    me = client.get("/api/v1/me", headers=headers)
    with SessionLocal() as db:
        user = db.get(User, uuid.UUID(me.json()["id"]))
        assert user is not None
        ensure_profile(db, user)
        db.expunge(user)
    return user


@pytest.mark.parametrize("prompt_id", PROMPTS)
def test_timeout_for_every_prompt(prompt_id: str) -> None:
    user = _user()
    fake = get_fake_provider()
    fake.delay_s = 1.0
    fake.script(prompt_id, {"ok": True, "note": "late"})
    with SessionLocal() as db:
        with pytest.raises(GatewayError) as err:
            complete(db, user, prompt_id, {}, _TinyOut, timeout=0.05)
        assert err.value.code == "unavailable"


@pytest.mark.parametrize("prompt_id", PROMPTS)
def test_daily_cap_for_every_prompt(prompt_id: str) -> None:
    user = _user()
    with SessionLocal() as db:
        for _ in range(settings.ai_daily_cap):
            db.add(
                AiCall(
                    user_id=user.id,
                    prompt_id=prompt_id,
                    prompt_version=1,
                    model="fake",
                    tokens_in=1,
                    tokens_out=1,
                    latency_ms=1,
                    outcome="ok",
                )
            )
        db.commit()
        with pytest.raises(GatewayError) as err:
            complete(db, user, prompt_id, {}, _TinyOut)
        assert err.value.status_code == 429
        assert err.value.code == "rate_limited"
