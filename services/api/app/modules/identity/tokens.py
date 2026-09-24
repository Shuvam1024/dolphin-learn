"""Verify access tokens from a managed issuer.

Development mints and checks HS256 tokens with AUTH_DEV_SECRET so tests and
local sign-in work without a hosted IdP. Production verifies RS256 via JWKS.
There is no password hash and no local credential store.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

import jwt
from app.config import settings
from app.errors import ApiError
from jwt import InvalidTokenError, PyJWKClient
from sqlalchemy.orm import Session

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
    now = int(time.time())
    payload = {
        "sub": subject,
        "email": email.strip().lower(),
        "iss": issuer(),
        "aud": audience(),
        "iat": now,
        "exp": now + 60 * 60,
        "jti": uuid.uuid4().hex,
    }
    secret = settings.auth_dev_secret or DEV_SECRET
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("ascii")


def decode_access_token(token: str, db: Session | None = None) -> dict[str, Any]:
    try:
        if settings.auth_jwks_url:
            key = PyJWKClient(settings.auth_jwks_url).get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=audience(),
                issuer=issuer(),
            )
        elif dev_tokens_enabled():
            secret = settings.auth_dev_secret or DEV_SECRET
            claims = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience=audience(),
                issuer=issuer(),
            )
        else:
            raise ApiError(
                "unauthorized",
                "Auth provider is not configured",
                status_code=401,
            )
    except ApiError:
        raise
    except InvalidTokenError as exc:
        raise ApiError("unauthorized", "Invalid token", status_code=401) from exc

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise ApiError("unauthorized", "Token missing subject", status_code=401)

    jti = claims.get("jti")
    if db is not None and isinstance(jti, str) and jti:
        from app.modules.identity.revocations import is_revoked

        if is_revoked(db, jti):
            raise ApiError("unauthorized", "Token revoked", status_code=401)
    return claims


def revoke_access_token(db: Session, token: str, *, user_id: uuid.UUID | None = None) -> None:
    """Blacklist the token jti until its exp. Idempotent."""
    from app.modules.identity.revocations import revoke_jti

    try:
        # Decode without revocation check so logout of an already-revoked token is fine.
        if settings.auth_jwks_url:
            key = PyJWKClient(settings.auth_jwks_url).get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=audience(),
                issuer=issuer(),
                options={"verify_exp": False},
            )
        else:
            secret = settings.auth_dev_secret or DEV_SECRET
            claims = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience=audience(),
                issuer=issuer(),
                options={"verify_exp": False},
            )
    except InvalidTokenError as exc:
        raise ApiError("unauthorized", "Invalid token", status_code=401) from exc

    jti = claims.get("jti")
    if not isinstance(jti, str) or not jti:
        # Tokens minted before jti still clear the cookie client-side.
        return
    exp = claims.get("exp")
    if isinstance(exp, (int, float)):
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    else:
        expires_at = datetime.now(timezone.utc)
    revoke_jti(db, jti=jti, expires_at=expires_at, user_id=user_id)
