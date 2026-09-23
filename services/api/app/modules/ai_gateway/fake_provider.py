"""Scripted provider for tests and CI. Supports adversarial outputs per prompt_id."""

from __future__ import annotations

import time
from typing import Any

from app.modules.ai_gateway.provider import Completion


class FakeProvider:
    def __init__(self) -> None:
        self.scripts: dict[str, list[dict[str, Any]]] = {}
        self.calls: list[str] = []
        self.opened_socket = False
        self.delay_s = 0.0

    def script(self, prompt_id: str, *outputs: dict[str, Any]) -> None:
        self.scripts[prompt_id] = list(outputs)

    def complete(
        self,
        prompt_id: str,
        variables: dict[str, Any],
        schema: dict[str, Any],
        *,
        timeout: float,
    ) -> Completion:
        _ = variables, schema
        self.calls.append(prompt_id)
        if self.delay_s > timeout:
            time.sleep(timeout)
            raise TimeoutError("fake provider timed out")
        if self.delay_s:
            time.sleep(self.delay_s)
        queue = self.scripts.get(prompt_id) or [{}]
        payload = queue.pop(0) if queue else {}
        if queue is not self.scripts.get(prompt_id):
            pass
        if prompt_id in self.scripts and not self.scripts[prompt_id]:
            # leave empty after consuming; next call returns {}
            pass
        return Completion(content=payload, model="fake", tokens_in=1, tokens_out=1, latency_ms=1)
