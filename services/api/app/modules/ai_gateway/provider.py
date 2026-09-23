"""AI gateway types and completion protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Completion:
    content: dict[str, Any]
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0


class Provider(Protocol):
    def complete(
        self,
        prompt_id: str,
        variables: dict[str, Any],
        schema: dict[str, Any],
        *,
        timeout: float,
    ) -> Completion: ...
