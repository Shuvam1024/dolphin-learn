"""Scripted provider for tests and CI. Supports adversarial outputs per prompt_id."""

from __future__ import annotations

import time
from typing import Any

from app.modules.ai_gateway.provider import Completion

_DEFAULTS: dict[str, dict[str, Any]] = {
    "ping": {"ok": True, "note": "pong"},
    "hint": {
        "hint": "Compare the choices to the idea in the reading without naming a letter.",
    },
    "explain_differently": {
        "explanation_markdown": (
            "Think of a name as a sticky note on a value — you can move the note later."
        ),
        "analogy_used": True,
    },
    "misconception_note": {
        "note": "That answer mixes up the roles in the idea.",
        "tag": "other",
    },
    "recall_compare": {
        "covered": ["names bind to values"],
        "missing": ["assignment rebinds"],
        "one_sentence_feedback": "You named binding; say what assignment changes.",
    },
}


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
        queue = self.scripts.get(prompt_id)
        if queue is not None:
            payload = queue.pop(0) if queue else {}
        else:
            payload = dict(_DEFAULTS.get(prompt_id, {}))
        return Completion(content=payload, model="fake", tokens_in=1, tokens_out=1, latency_ms=1)
