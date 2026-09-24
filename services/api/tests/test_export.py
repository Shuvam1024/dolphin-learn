"""S98: export my data — opaque to other users, no raw prompts."""

from __future__ import annotations

import uuid

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _user(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def test_export_two_user_isolation() -> None:
    with SessionLocal() as db:
        seed(db)
    a = _user("s98a")
    b = _user("s98b")
    client.post(
        "/api/v1/goals",
        headers=a,
        json={
            "title": "A only",
            "domain_key": "python",
            "raw_request": "secret for a",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 60,
                "preferred_session_minutes": 25,
            },
        },
    )
    export_a = client.get("/api/v1/me/export", headers=a)
    assert export_a.status_code == 200, export_a.text
    body_a = export_a.json()
    assert body_a["user"]["email"].endswith("@example.com")
    assert any(g["title"] == "A only" for g in body_a["goals"])
    assert "ai_calls" in body_a
    assert "effort_factors" in body_a
    # No raw prompt field on AI audit
    for row in body_a["ai_calls"]:
        assert "prompt" not in row or row.get("prompt") is None

    export_b = client.get("/api/v1/me/export", headers=b)
    assert export_b.status_code == 200
    assert all(g["title"] != "A only" for g in export_b.json()["goals"])
    assert "secret for a" not in export_b.text


def test_export_rate_limit() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _user("s98rate")
    for _ in range(3):
        assert client.get("/api/v1/me/export", headers=headers).status_code == 200
    limited = client.get("/api/v1/me/export", headers=headers)
    assert limited.status_code == 429
