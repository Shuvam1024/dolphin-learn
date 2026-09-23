"""S12: a learner reads and updates only their own preferences."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.identity.models import User
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


def _token(email: str) -> str:
    issued = client.post("/api/v1/dev/token", json={"email": email})
    assert issued.status_code == 200
    return issued.json()["access_token"]


def test_owner_can_read_and_patch_preferences() -> None:
    email = f"s12-{uuid.uuid4().hex[:8]}@example.com"
    headers = {"Authorization": f"Bearer {_token(email)}"}

    initial = client.get("/api/v1/me", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["profile"]["timezone"] == "UTC"
    assert initial.json()["profile"]["locale"] == "en"

    patched = client.patch(
        "/api/v1/me/preferences",
        headers=headers,
        json={
            "display_name": "Ada",
            "timezone": "America/New_York",
            "locale": "en-US",
            "a11y_prefs": {"reduced_motion": True, "larger_text": False},
        },
    )
    assert patched.status_code == 200
    profile = patched.json()["profile"]
    assert profile["display_name"] == "Ada"
    assert profile["timezone"] == "America/New_York"
    assert profile["locale"] == "en-US"
    assert profile["a11y_prefs"]["reduced_motion"] is True

    again = client.get("/api/v1/me", headers=headers)
    assert again.json()["profile"]["timezone"] == "America/New_York"


def test_cannot_retarget_another_user() -> None:
    email_a = f"s12-a-{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"s12-b-{uuid.uuid4().hex[:8]}@example.com"
    headers_a = {"Authorization": f"Bearer {_token(email_a)}"}
    headers_b = {"Authorization": f"Bearer {_token(email_b)}"}

    me_a = client.get("/api/v1/me", headers=headers_a).json()
    client.patch(
        "/api/v1/me/preferences",
        headers=headers_a,
        json={"timezone": "Europe/Paris"},
    )

    forbidden = client.patch(
        "/api/v1/me/preferences",
        headers=headers_b,
        json={"user_id": me_a["id"], "timezone": "Pacific/Auckland"},
    )
    assert forbidden.status_code == 422

    still = client.get("/api/v1/me", headers=headers_a)
    assert still.json()["profile"]["timezone"] == "Europe/Paris"

    with SessionLocal() as db:
        user_a = db.scalar(select(User).where(User.email == email_a))
        assert user_a is not None
        assert user_a.id == uuid.UUID(me_a["id"])


def test_rejects_invalid_timezone() -> None:
    headers = {"Authorization": f"Bearer {_token(f's12-bad-{uuid.uuid4().hex[:8]}@example.com')}"}
    response = client.patch(
        "/api/v1/me/preferences",
        headers=headers,
        json={"timezone": "Not/AZone"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
