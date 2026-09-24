"""One door for every model call: enablement, limits, audit, validation."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings
from app.modules.ai_gateway.fake_provider import FakeProvider
from app.modules.ai_gateway.http_provider import HttpProvider
from app.modules.ai_gateway.models import AiCall
from app.modules.ai_gateway.provider import Completion, Provider
from app.modules.ai_gateway.schemas import GatewayError, validate_against_model
from app.modules.identity.models import LearnerProfile, User
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
_TOKENISH = re.compile(r"\b(?:sk|tok|Bearer)[-_A-Za-z0-9]{8,}\b")

_provider: Provider | None = None
_fake = FakeProvider()


def get_fake_provider() -> FakeProvider:
    return _fake


def reset_provider() -> None:
    global _provider
    _provider = None


def _build_provider() -> Provider:
    if settings.ai_provider == "fake":
        return _fake
    if settings.ai_provider == "http":
        return HttpProvider()
    return _fake


def current_provider() -> Provider:
    global _provider
    if _provider is None:
        _provider = _build_provider()
    return _provider


def redact(variables: dict[str, Any]) -> dict[str, Any]:
    def scrub(value: Any) -> Any:
        if isinstance(value, str):
            cleaned = _EMAIL.sub("[redacted-email]", value)
            return _TOKENISH.sub("[redacted-token]", cleaned)
        if isinstance(value, dict):
            return {key: scrub(item) for key, item in value.items()}
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value

    return scrub(variables)


def is_enabled(db: Session | None = None, user: User | None = None) -> bool:
    if not settings.ai_gateway_enabled:
        return False
    if settings.ai_provider in ("", "off", "none"):
        return False
    if user is not None and db is not None:
        profile = db.get(LearnerProfile, user.id)
        if profile is not None and profile.ai_opt_out:
            return False
    return True


def _daily_count(db: Session, user_id: uuid.UUID) -> int:
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return int(
        db.scalar(
            select(func.count())
            .select_from(AiCall)
            .where(
                AiCall.user_id == user_id,
                AiCall.created_at >= start,
                AiCall.created_at < end,
                AiCall.outcome == "ok",
            )
        )
        or 0
    )


def _audit(
    db: Session | None,
    *,
    user_id: uuid.UUID | None,
    prompt_id: str,
    prompt_version: int,
    model: str,
    tokens_in: int,
    tokens_out: int,
    latency_ms: int,
    outcome: str,
) -> None:
    if db is None:
        return
    db.add(
        AiCall(
            user_id=user_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            outcome=outcome,
        )
    )
    db.commit()


def complete(
    db: Session | None,
    user: User | None,
    prompt_id: str,
    variables: dict[str, Any],
    output_model: type[BaseModel],
    *,
    prompt_version: int = 1,
    timeout: float | None = None,
) -> BaseModel:
    timeout = settings.ai_timeout_s if timeout is None else timeout
    if not is_enabled(db, user):
        _audit(
            db,
            user_id=user.id if user else None,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            model="none",
            tokens_in=0,
            tokens_out=0,
            latency_ms=0,
            outcome="disabled",
        )
        raise GatewayError("unavailable", "AI is not enabled", status_code=503)

    if db is not None and user is not None:
        if _daily_count(db, user.id) >= settings.ai_daily_cap:
            _audit(
                db,
                user_id=user.id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
                model=settings.ai_model,
                tokens_in=0,
                tokens_out=0,
                latency_ms=0,
                outcome="capped",
            )
            raise GatewayError("rate_limited", "Daily AI limit reached", status_code=429)

    safe_vars = redact(variables)
    schema = output_model.model_json_schema()
    provider = current_provider()
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            result: Completion = provider.complete(
                prompt_id, safe_vars, schema, timeout=timeout
            )
            parsed = validate_against_model(output_model, result.content)
            _audit(
                db,
                user_id=user.id if user else None,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
                model=result.model,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                latency_ms=result.latency_ms,
                outcome="ok",
            )
            from app.observability import record_ai_metric

            record_ai_metric(
                prompt_id,
                latency_ms=result.latency_ms,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
            )
            return parsed
        except GatewayError as exc:
            last_error = exc
            if exc.code == "schema_error":
                from app.observability import record_ai_metric

                record_ai_metric(prompt_id, latency_ms=0, validator_reject=True)
            if exc.code != "schema_error":
                break
        except TimeoutError as exc:
            last_error = GatewayError("unavailable", "AI timed out", status_code=503)
            _ = exc
            break
        except Exception as exc:  # noqa: BLE001 — provider failures become unavailable
            last_error = GatewayError("unavailable", "AI provider failed", status_code=503)
            _ = exc
            break

    outcome = (
        "schema_error"
        if isinstance(last_error, GatewayError) and last_error.code == "schema_error"
        else "unavailable"
    )
    _audit(
        db,
        user_id=user.id if user else None,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        model=settings.ai_model,
        tokens_in=0,
        tokens_out=0,
        latency_ms=int(timeout * 1000),
        outcome=outcome,
    )
    if isinstance(last_error, GatewayError):
        raise last_error
    raise GatewayError("unavailable", "AI provider failed", status_code=503)
