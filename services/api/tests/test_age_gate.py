"""S13: adult acknowledgment is stored and required before goal creation on the client."""

import uuid

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def _headers(email: str) -> dict[str, str]:
    issued = client.post("/api/v1/dev/token", json={"email": email})
    assert issued.status_code == 200
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def test_acknowledgment_persists() -> None:
    headers = _headers(f"s13-{uuid.uuid4().hex[:8]}@example.com")
    before = client.get("/api/v1/me", headers=headers)
    assert before.status_code == 200
    assert before.json()["profile"]["adult_acknowledged_at"] is None

    recorded = client.post("/api/v1/me/adult-acknowledgment", headers=headers)
    assert recorded.status_code == 200
    stamp = recorded.json()["profile"]["adult_acknowledged_at"]
    assert stamp

    again = client.get("/api/v1/me", headers=headers)
    assert again.json()["profile"]["adult_acknowledged_at"] == stamp

    repeat = client.post("/api/v1/me/adult-acknowledgment", headers=headers)
    assert repeat.json()["profile"]["adult_acknowledged_at"] == stamp
