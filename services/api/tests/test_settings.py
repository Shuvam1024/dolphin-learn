"""S96: settings preferences — sitting length, a11y, tutor on/off."""

from __future__ import annotations

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.identity.models import LearnerProfile
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def test_settings_preferences_persist_and_toggle_tutor() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s96")
    patched = client.patch(
        "/api/v1/me/preferences",
        headers=headers,
        json={
            "display_name": "Alex",
            "timezone": "America/New_York",
            "default_session_minutes": 40,
            "a11y_prefs": {"larger_text": True, "reduced_motion": True},
            "use_tutor": False,
        },
    )
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert body["profile"]["display_name"] == "Alex"
    assert body["profile"]["timezone"] == "America/New_York"
    assert body["profile"]["default_session_minutes"] == 40
    assert body["profile"]["a11y_prefs"]["larger_text"] is True
    assert body["profile"]["a11y_prefs"]["reduced_motion"] is True
    assert body["profile"]["use_tutor"] is False
    assert body["profile"]["ai_opt_out"] is True
    assert body["ai_enabled"] is False

    me = client.get("/api/v1/me", headers=headers).json()
    assert me["profile"]["default_session_minutes"] == 40
    assert me["ai_enabled"] is False

    user_id = me["id"]
    with SessionLocal() as db:
        profile = db.get(LearnerProfile, uuid.UUID(user_id))
        assert profile is not None
        assert profile.default_session_minutes == 40
        assert profile.ai_opt_out is True


def test_default_session_minutes_bounds() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s96-bounds")
    too_low = client.patch(
        "/api/v1/me/preferences",
        headers=headers,
        json={"default_session_minutes": 2},
    )
    assert too_low.status_code == 422
    too_high = client.patch(
        "/api/v1/me/preferences",
        headers=headers,
        json={"default_session_minutes": 200},
    )
    assert too_high.status_code == 422
