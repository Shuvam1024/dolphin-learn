"""Simple in-memory rate limits for sensitive API routes (S100)."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# path prefix → (max requests, window seconds)
LIMITS: dict[str, tuple[int, int]] = {
    "/api/v1/dev/token": (30, 60),
    "/api/v1/sessions": (120, 60),
    "/api/v1/auth/revoke": (30, 60),
}

_HITS: dict[str, deque[float]] = defaultdict(deque)


def clear_rate_limits() -> None:
    _HITS.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        path = request.url.path
        matched: tuple[str, tuple[int, int]] | None = None
        for prefix, rule in LIMITS.items():
            if path == prefix or path.startswith(prefix + "/"):
                if matched is None or len(prefix) > len(matched[0]):
                    matched = (prefix, rule)
        if "/hint" in path or path.endswith("/explain"):
            matched = (path, (60, 60))

        if matched is not None:
            limit, window = matched[1]
            key = f"{request.client.host if request.client else 'unknown'}:{matched[0]}"
            now = time.time()
            bucket = _HITS[key]
            while bucket and bucket[0] <= now - window:
                bucket.popleft()
            if len(bucket) >= limit:
                request_id = str(uuid.uuid4())
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "rate_limited",
                            "message": "Too many requests",
                            "details": None,
                            "request_id": request_id,
                        }
                    },
                )
            bucket.append(now)

        return await call_next(request)
