"""Structured logs, AI metrics, and readiness (S102)."""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import time
from collections import defaultdict
from typing import Any

from app.config import settings
from app.db import engine
from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("dolphin.api")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

_security = HTTPBasic(auto_error=False)
router = APIRouter()

# prompt_id → list of latency_ms and counters
_METRICS: dict[str, dict[str, Any]] = defaultdict(
    lambda: {
        "calls": 0,
        "latencies": [],
        "fallback": 0,
        "validator_reject": 0,
        "tokens_in": 0,
        "tokens_out": 0,
    }
)


def record_ai_metric(
    prompt_id: str,
    *,
    latency_ms: int,
    tokens_in: int = 0,
    tokens_out: int = 0,
    fallback: bool = False,
    validator_reject: bool = False,
) -> None:
    row = _METRICS[prompt_id]
    row["calls"] += 1
    row["latencies"].append(int(latency_ms))
    row["tokens_in"] += int(tokens_in)
    row["tokens_out"] += int(tokens_out)
    if fallback:
        row["fallback"] += 1
    if validator_reject:
        row["validator_reject"] += 1


def _p95(values: list[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, int(round(0.95 * (len(ordered) - 1))))
    return int(ordered[index])


def metrics_snapshot() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for prompt_id, row in _METRICS.items():
        calls = max(1, int(row["calls"]))
        out[prompt_id] = {
            "calls": row["calls"],
            "p95_latency_ms": _p95(list(row["latencies"])),
            "fallback_rate": row["fallback"] / calls,
            "validator_rejection_rate": row["validator_reject"] / calls,
            "tokens_in": row["tokens_in"],
            "tokens_out": row["tokens_out"],
        }
    return out


def reset_metrics() -> None:
    _METRICS.clear()


class StructuredLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - started) * 1000)
        auth = request.headers.get("authorization", "")
        user_hash = ""
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
            # Redact token; store only a short hash of the bearer material.
            user_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]
        payload = {
            "request_id": getattr(request.state, "request_id", None),
            "route": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "user_hash": user_hash,
        }
        # Never log raw Authorization headers.
        logger.info(json.dumps(payload))
        return response


def _metrics_auth(credentials: HTTPBasicCredentials | None = Depends(_security)) -> None:
    user = getattr(settings, "metrics_user", "metrics") or "metrics"
    password = getattr(settings, "metrics_password", "changeme") or "changeme"
    if credentials is None:
        from app.errors import ApiError

        raise ApiError("unauthorized", "Metrics auth required", status_code=401)
    ok_user = secrets.compare_digest(credentials.username, user)
    ok_pass = secrets.compare_digest(credentials.password, password)
    if not (ok_user and ok_pass):
        from app.errors import ApiError

        raise ApiError("unauthorized", "Metrics auth required", status_code=401)


@router.get("/metrics")
def metrics(_: None = Depends(_metrics_auth)) -> dict[str, Any]:
    return {"prompts": metrics_snapshot()}


def ready_check() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready"}
