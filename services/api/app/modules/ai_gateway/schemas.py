"""Shared pydantic helpers for AI gateway outputs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError


class GatewayError(Exception):
    def __init__(self, code: str, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def validate_against_model(model: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise GatewayError("schema_error", "Model output failed schema validation") from exc


class EmptyOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
