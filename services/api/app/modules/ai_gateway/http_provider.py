"""OpenAI-compatible HTTP provider. Only used when AI_PROVIDER=http."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
from app.config import settings
from app.modules.ai_gateway.provider import Completion


class HttpProvider:
    def complete(
        self,
        prompt_id: str,
        variables: dict[str, Any],
        schema: dict[str, Any],
        *,
        timeout: float,
    ) -> Completion:
        started = time.perf_counter()
        body = {
            "model": settings.ai_model,
            "messages": [
                {"role": "system", "content": f"prompt:{prompt_id}"},
                {
                    "role": "user",
                    "content": json.dumps({"variables": variables, "schema": schema}),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {settings.ai_api_key}"}
        with httpx.Client(base_url=settings.ai_base_url, timeout=timeout) as client:
            response = client.post("/chat/completions", json=body, headers=headers)
            response.raise_for_status()
            data = response.json()
        content_raw = data["choices"][0]["message"]["content"]
        content = json.loads(content_raw) if isinstance(content_raw, str) else content_raw
        usage = data.get("usage") or {}
        latency_ms = int((time.perf_counter() - started) * 1000)
        return Completion(
            content=content,
            model=str(data.get("model") or settings.ai_model),
            tokens_in=int(usage.get("prompt_tokens") or 0),
            tokens_out=int(usage.get("completion_tokens") or 0),
            latency_ms=latency_ms,
        )
