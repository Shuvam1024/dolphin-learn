"""Shared API error envelope.

Every failure the client can see uses the same shape:

    {"error": {"code", "message", "details", "request_id"}}
"""

from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request
from fastapi.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"

_STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    500: "internal_error",
}


class ApiError(Exception):
    """Domain or auth failure that should become the standard envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: object | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def status_code_name(status_code: int) -> str:
    return _STATUS_CODES.get(status_code, "http_error")


def error_payload(
    code: str,
    message: str,
    request: Request,
    details: object | None = None,
) -> dict[str, dict[str, object]]:
    request_id = getattr(request.state, "request_id", None) or str(uuid4())
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    incoming = request.headers.get(REQUEST_ID_HEADER)
    request.state.request_id = incoming or str(uuid4())
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request.state.request_id
    return response
