"""S100: API rate limits return a 429 envelope."""

from __future__ import annotations

from app.main import app
from app.rate_limit import clear_rate_limits
from fastapi.testclient import TestClient

client = TestClient(app, raise_server_exceptions=False)


def test_dev_token_rate_limit_envelope(monkeypatch) -> None:
    clear_rate_limits()
    monkeypatch.setitem(
        __import__("app.rate_limit", fromlist=["LIMITS"]).LIMITS,
        "/api/v1/dev/token",
        (3, 60),
    )
    last = None
    for index in range(5):
        last = client.post(
            "/api/v1/dev/token",
            json={"email": f"rate-{index}@example.com"},
        )
    assert last is not None
    assert last.status_code == 429
    body = last.json()
    assert body["error"]["code"] == "rate_limited"
    clear_rate_limits()
