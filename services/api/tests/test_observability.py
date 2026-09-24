"""S102: structured logs redact tokens; metrics count fake calls; /ready needs DB."""

from __future__ import annotations

import base64
import io
import logging
import uuid

from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.modules.ai_gateway.service import complete, get_fake_provider, reset_provider
from app.modules.identity.models import User
from app.modules.identity.service import ensure_profile
from app.observability import metrics_snapshot, reset_metrics
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

client = TestClient(app)


class PingOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True


def test_logs_redact_bearer_tokens(caplog, monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", False)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s102-{uuid.uuid4().hex[:8]}@example.com"},
    )
    token = issued.json()["access_token"]
    with caplog.at_level(logging.INFO, logger="dolphin.api"):
        client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    blob = " ".join(record.message for record in caplog.records)
    assert token not in blob
    assert "Bearer " not in blob


def test_metrics_count_fake_calls(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(settings, "ai_provider", "fake")
    reset_provider()
    reset_metrics()
    fake = get_fake_provider()
    fake.script("ping", {"ok": True})
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s102m-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    me = client.get("/api/v1/me", headers=headers).json()
    with SessionLocal() as db:
        user = db.get(User, uuid.UUID(me["id"]))
        assert user is not None
        ensure_profile(db, user)
        complete(db, user, "ping", {}, PingOut)
    snap = metrics_snapshot()
    assert snap["ping"]["calls"] >= 1
    auth = base64.b64encode(
        f"{settings.metrics_user}:{settings.metrics_password}".encode()
    ).decode()
    metrics = client.get("/metrics", headers={"Authorization": f"Basic {auth}"})
    assert metrics.status_code == 200
    assert metrics.json()["prompts"]["ping"]["calls"] >= 1


def test_ready_requires_db(monkeypatch) -> None:
    ok = client.get("/ready")
    assert ok.status_code == 200
    assert ok.json()["status"] == "ready"

    def boom() -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr("app.observability.engine.connect", boom)
    soft = TestClient(app, raise_server_exceptions=False)
    down = soft.get("/ready")
    assert down.status_code == 503
    assert down.json()["error"]["code"] == "unavailable"
