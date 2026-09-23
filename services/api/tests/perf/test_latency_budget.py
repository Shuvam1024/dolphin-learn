"""S51: deterministic API endpoints stay within a 250 ms p95 budget."""

from __future__ import annotations

import os
import statistics
import time

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    os.environ.get("DOLPHIN_PERF") != "1",
    reason="Set DOLPHIN_PERF=1 to run latency budgets",
)

BUDGET_MS = 250
CALLS = 50


def _p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
    return ordered[index]


def _time_calls(label: str, fn) -> float:
    samples: list[float] = []
    for _ in range(CALLS):
        start = time.perf_counter()
        response = fn()
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert response.status_code == 200, response.text
        samples.append(elapsed_ms)
    p95 = _p95(samples)
    mean = statistics.fmean(samples)
    print(f"perf api {label}: p95={p95:.1f}ms mean={mean:.1f}ms n={CALLS}")
    return p95


def test_home_latency(heavy_learner: dict[str, object], api_client: TestClient) -> None:
    headers = heavy_learner["headers"]  # type: ignore[assignment]

    def call():
        return api_client.get("/api/v1/home", headers=headers)

    assert _time_calls("home", call) <= BUDGET_MS


def test_progress_latency(heavy_learner: dict[str, object], api_client: TestClient) -> None:
    headers = heavy_learner["headers"]  # type: ignore[assignment]

    def call():
        return api_client.get("/api/v1/progress", headers=headers)

    assert _time_calls("progress", call) <= BUDGET_MS


def test_reviews_due_latency(heavy_learner: dict[str, object], api_client: TestClient) -> None:
    headers = heavy_learner["headers"]  # type: ignore[assignment]

    def call():
        return api_client.get("/api/v1/reviews/due", headers=headers)

    assert _time_calls("reviews/due", call) <= BUDGET_MS


def test_overview_latency(heavy_learner: dict[str, object], api_client: TestClient) -> None:
    headers = heavy_learner["headers"]  # type: ignore[assignment]
    goal_id = heavy_learner["goal_id"]

    def call():
        return api_client.get(f"/api/v1/goals/{goal_id}/overview", headers=headers)

    assert _time_calls("overview", call) <= BUDGET_MS


def test_session_latency(heavy_learner: dict[str, object], api_client: TestClient) -> None:
    headers = heavy_learner["headers"]  # type: ignore[assignment]
    session_id = heavy_learner["session_id"]

    def call():
        return api_client.get(f"/api/v1/sessions/{session_id}", headers=headers)

    assert _time_calls("session", call) <= BUDGET_MS


def test_plan_proposals_latency(heavy_learner: dict[str, object], api_client: TestClient) -> None:
    headers = heavy_learner["headers"]  # type: ignore[assignment]
    goal_id = heavy_learner["goal_id"]

    def call():
        return api_client.post(
            f"/api/v1/goals/{goal_id}/plan-proposals",
            headers=headers,
            json={},
        )

    assert _time_calls("plan-proposals", call) <= BUDGET_MS
