"""S56: AI gateway enablement, schema, limits, audit, and no-socket when off."""

from __future__ import annotations

import uuid

import pytest
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.modules.ai_gateway.models import AiCall
from app.modules.ai_gateway.schemas import GatewayError
from app.modules.ai_gateway.service import (
    complete,
    get_fake_provider,
    is_enabled,
    redact,
    reset_provider,
)
from app.modules.identity.models import LearnerProfile, User
from app.modules.identity.service import ensure_profile
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

client = TestClient(app)


class PingOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    note: str = Field(max_length=40)


@pytest.fixture(autouse=True)
def _ai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(settings, "ai_provider", "fake")
    monkeypatch.setattr(settings, "ai_daily_cap", 50)
    monkeypatch.setattr(settings, "ai_timeout_s", 0.2)
    reset_provider()
    fake = get_fake_provider()
    fake.scripts.clear()
    fake.calls.clear()
    fake.delay_s = 0.0
    yield
    reset_provider()


def _user() -> tuple[User, dict[str, str]]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s56-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    me = client.get("/api/v1/me", headers=headers)
    with SessionLocal() as db:
        user = db.get(User, uuid.UUID(me.json()["id"]))
        assert user is not None
        ensure_profile(db, user)
        db.expunge(user)
    return user, headers


def test_schema_violation_is_typed_error() -> None:
    user, _headers = _user()
    fake = get_fake_provider()
    fake.script("ping", {"ok": "nope"})
    with SessionLocal() as db:
        with pytest.raises(GatewayError) as err:
            complete(db, user, "ping", {"x": 1}, PingOut)
        assert err.value.code == "schema_error"
        row = db.scalar(
            select(AiCall)
            .where(AiCall.user_id == user.id)
            .order_by(AiCall.created_at.desc())
        )
        assert row is not None
        assert row.outcome == "schema_error"
        assert "prompt" not in (row.prompt_id + row.model)


def test_timeout_becomes_unavailable() -> None:
    user, _headers = _user()
    fake = get_fake_provider()
    fake.delay_s = 1.0
    fake.script("ping", {"ok": True, "note": "hi"})
    with SessionLocal() as db:
        with pytest.raises(GatewayError) as err:
            complete(db, user, "ping", {}, PingOut, timeout=0.05)
        assert err.value.code == "unavailable"


def test_daily_cap_returns_429_envelope() -> None:
    user, _headers = _user()
    with SessionLocal() as db:
        for _ in range(settings.ai_daily_cap):
            db.add(
                AiCall(
                    user_id=user.id,
                    prompt_id="ping",
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
            complete(db, user, "ping", {}, PingOut)
        assert err.value.status_code == 429
        assert err.value.code == "rate_limited"


def test_flag_off_or_opt_out_never_calls_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    user, headers = _user()
    fake = get_fake_provider()
    fake.script("ping", {"ok": True, "note": "hi"})
    called = {"n": 0}
    original = fake.complete

    def guarded(*args: object, **kwargs: object) -> object:
        called["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fake, "complete", guarded)

    monkeypatch.setattr(settings, "ai_gateway_enabled", False)
    reset_provider()
    with SessionLocal() as db:
        assert is_enabled(db, user) is False
        with pytest.raises(GatewayError):
            complete(db, user, "ping", {}, PingOut)
    assert called["n"] == 0
    me = client.get("/api/v1/me", headers=headers)
    assert me.json()["ai_enabled"] is False

    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(settings, "ai_provider", "fake")
    reset_provider()
    with SessionLocal() as db:
        profile = db.get(LearnerProfile, user.id)
        assert profile is not None
        profile.ai_opt_out = True
        db.commit()
        user2 = db.get(User, user.id)
        assert is_enabled(db, user2) is False
        with pytest.raises(GatewayError):
            complete(db, user2, "ping", {}, PingOut)
    assert called["n"] == 0


def test_audit_row_has_no_raw_prompt() -> None:
    user, _headers = _user()
    fake = get_fake_provider()
    fake.script("ping", {"ok": True, "note": "hi"})
    with SessionLocal() as db:
        out = complete(
            db,
            user,
            "ping",
            {"email": "secret@example.com", "token": "sk-abcdefghijk"},
            PingOut,
        )
        assert out.ok is True
        row = db.scalar(
            select(AiCall)
            .where(AiCall.user_id == user.id)
            .order_by(AiCall.created_at.desc())
        )
        assert row is not None
        assert row.outcome == "ok"
        assert "secret@example.com" not in str(row.__dict__)
    redacted = redact({"email": "a@b.co", "token": "sk-abcdefghijk"})
    assert "a@b.co" not in str(redacted)
    assert "sk-abcdefghijk" not in str(redacted)
