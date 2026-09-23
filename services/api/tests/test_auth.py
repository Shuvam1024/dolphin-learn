"""S10: a valid test token resolves a user; a missing token is 401."""

from app.db import SessionLocal
from app.main import app
from app.modules.identity.models import User
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def test_me_requires_auth() -> None:
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "unauthorized"
    assert error["request_id"]


def test_dev_token_creates_user_once() -> None:
    email = "s10-learner@example.com"
    issued = client.post("/api/v1/dev/token", json={"email": email})
    assert issued.status_code == 200
    token = issued.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    first = client.get("/api/v1/me", headers=headers)
    assert first.status_code == 200
    body = first.json()
    assert body["email"] == email
    assert body["auth_subject"] == "dev|s10-learner@example.com"

    second = client.get("/api/v1/me", headers=headers)
    assert second.status_code == 200
    assert second.json()["id"] == body["id"]

    with SessionLocal() as db:
        count = db.scalar(
            select(func.count()).select_from(User).where(User.auth_subject == body["auth_subject"])
        )
    assert count == 1
