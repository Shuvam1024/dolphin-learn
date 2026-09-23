"""Verify access tokens from a managed issuer.

Development mints and checks HS256 tokens with AUTH_DEV_SECRET so tests and
local sign-in work without a hosted IdP. Production verifies RS256 via JWKS.
There is no password hash and no local credential store.
"""

from __future__ import annotations

import time
from typing import Any

import jwt
from app.config import settings
from app.errors import ApiError
from jwt import InvalidTokenError, PyJWKClient

DEV_ISSUER = "https://dolphin.local/dev"
DEV_AUDIENCE = "dolphin-api"
DEV_SECRET = "dev-only-not-a-password"


def issuer() -> str:
    return settings.auth_issuer_url or DEV_ISSUER


def audience() -> str:
    return settings.auth_audience or DEV_AUDIENCE


def dev_tokens_enabled() -> bool:
    return settings.environment != "production"


def issue_dev_token(*, email: str) -> str:
    """Sign a short-lived dev token. Refused when ENVIRONMENT=production."""
    if not dev_tokens_enabled():
        raise ApiError("not_found", "Not Found", status_code=404)
    subject = f"dev|{email.strip().lower()}"
    payload = {
        "sub": subject,
        "email": email.strip().lower(),
        "iss": issuer(),
        "aud": audience(),
        "exp": int(time.time()) + 60 * 60,
    }
    secret = settings.auth_dev_secret or DEV_SECRET
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("ascii")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        if dev_tokens_enabled():
            secret = settings.auth_dev_secret or DEV_SECRET
            claims = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience=audience(),
                issuer=issuer(),
            )
        else:
            if not settings.auth_jwks_url:
                raise ApiError(
                    "unauthorized",
                    "Auth provider is not configured",
                    status_code=401,
                )
            key = PyJWKClient(settings.auth_jwks_url).get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=audience(),
                issuer=issuer(),
            )
    except ApiError:
        raise
    except InvalidTokenError as exc:
        raise ApiError("unauthorized", "Invalid token", status_code=401) from exc

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise ApiError("unauthorized", "Token missing subject", status_code=401)
    return claims
