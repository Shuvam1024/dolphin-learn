"""S97: production auth uses RS256 JWKS; dev token gated; logout revokes."""

from __future__ import annotations

import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

import jwt
import pytest
from app.config import settings
from app.main import app
from app.modules.identity.tokens import decode_access_token
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture()
def rsa_jwks(monkeypatch: pytest.MonkeyPatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()

    def _b64url_uint(value: int) -> str:
        length = (value.bit_length() + 7) // 8
        return jwt.utils.base64url_encode(value.to_bytes(length, "big")).decode("ascii")

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "s97-test",
                "use": "sig",
                "alg": "RS256",
                "n": _b64url_uint(public_numbers.n),
                "e": _b64url_uint(public_numbers.e),
            }
        ]
    }
    payload = json.dumps(jwks).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    jwks_url = f"http://{host}:{port}/jwks.json"

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "auth_jwks_url", jwks_url)
    monkeypatch.setattr(settings, "auth_issuer_url", "https://auth.example.com/")
    monkeypatch.setattr(settings, "auth_audience", "dolphin-api")

    yield private_key, jwks_url

    server.shutdown()
    thread.join(timeout=2)


def test_dev_token_disabled_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "auth_jwks_url", "")
    response = client.post("/api/v1/dev/token", json={"email": "prod@example.com"})
    assert response.status_code == 404


def test_rs256_jwks_token_accepted(rsa_jwks) -> None:
    private_key, _jwks = rsa_jwks
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": f"oidc|{uuid.uuid4().hex[:8]}",
            "email": f"s97-{uuid.uuid4().hex[:6]}@example.com",
            "iss": "https://auth.example.com/",
            "aud": "dolphin-api",
            "iat": now,
            "exp": now + 3600,
            "jti": uuid.uuid4().hex,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "s97-test"},
    )
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text
    assert me.json()["email"].endswith("@example.com")


def test_logout_revokes_token() -> None:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s97-revoke-{uuid.uuid4().hex[:8]}@example.com"},
    )
    assert issued.status_code == 200
    token = issued.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/me", headers=headers).status_code == 200
    revoked = client.post("/api/v1/auth/revoke", headers=headers)
    assert revoked.status_code == 200
    assert client.get("/api/v1/me", headers=headers).status_code == 401


def test_no_password_routes_or_fields() -> None:
    openapi = client.get("/openapi.json").json()
    for schema in (openapi.get("components") or {}).get("schemas", {}).values():
        props = schema.get("properties") or {}
        assert "password" not in props
    # Dev token body is email-only.
    issued = client.post("/api/v1/dev/token", json={"email": "nopw@example.com", "password": "x"})
    assert issued.status_code == 422


def test_decode_requires_jwks_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "auth_jwks_url", "")
    from app.errors import ApiError

    with pytest.raises(ApiError) as err:
        decode_access_token("not.a.token")
    assert err.value.status_code == 401
