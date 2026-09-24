"""S99: delete account with confirmation and retention."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.db import SessionLocal
from app.jobs.purge import purge_due_accounts
from app.main import app
from app.modules.ai_gateway.models import AiCall
from app.modules.identity.models import User
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def test_delete_requires_confirm_and_tombstones() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s99-{uuid.uuid4().hex[:8]}@example.com"},
    )
    token = issued.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    bad = client.request("DELETE", "/api/v1/me", headers=headers, json={"confirm": "nope"})
    assert bad.status_code == 422
    ok = client.request("DELETE", "/api/v1/me", headers=headers, json={"confirm": "DELETE"})
    assert ok.status_code == 200, ok.text
    assert ok.json()["retention_days"] == settings.retention_days
    assert client.get("/api/v1/me", headers=headers).status_code == 401


def test_purge_anonymizes_ai_and_removes_user(monkeypatch) -> None:
    with SessionLocal() as db:
        seed(db)
        user = User(auth_subject=f"deleted|{uuid.uuid4().hex}", email="gone@invalid.local")
        user.deleted_at = datetime.now(timezone.utc) - timedelta(days=31)
        db.add(user)
        db.flush()
        db.add(
            AiCall(
                user_id=user.id,
                prompt_id="hint",
                prompt_version=1,
                model="fake",
                tokens_in=1,
                tokens_out=1,
                latency_ms=1,
                outcome="ok",
            )
        )
        user_id = user.id
        db.commit()

    monkeypatch.setattr(settings, "retention_days", 30)
    assert purge_due_accounts() >= 1
    with SessionLocal() as db:
        assert db.get(User, user_id) is None
        from sqlalchemy import select

        anon = db.scalar(select(AiCall).where(AiCall.model == "anonymized").limit(1))
        assert anon is not None
        assert anon.user_id is None
