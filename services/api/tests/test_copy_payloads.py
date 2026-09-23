"""S53: learner-facing payloads carry names and plain reasons beside keys."""

from __future__ import annotations

import uuid
from typing import Any

from app.db import SessionLocal
from app.main import app
from app.modules.learning.copy import FACET_LABEL, REASON_TEXT
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _walk(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(_walk(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk(child))
    return found


def _assert_named_payloads(body: object) -> None:
    for node in _walk(body):
        if "competency_key" in node:
            assert "competency_name" in node, node
            assert isinstance(node["competency_name"], str)
            assert node["competency_name"].strip(), node
        if node.get("reason_code"):
            assert "reason_text" in node, node
            assert node["reason_text"] == REASON_TEXT[node["reason_code"]], node
        if node.get("status_facet"):
            assert "facet_label" in node, node
            assert node["facet_label"] == FACET_LABEL[node["status_facet"]], node


def test_copy_payloads_carry_names_and_reason_text() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s53")

    short = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Short Python",
            "domain_key": "python",
            "raw_request": "Names and calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 15,
                "preferred_session_minutes": 15,
            },
        },
    )
    short_id = short.json()["id"]
    proposed = client.post(f"/api/v1/goals/{short_id}/plan-proposals", headers=headers, json={})
    assert proposed.status_code == 200
    _assert_named_payloads(proposed.json())
    assert proposed.json()["deferred"]
    assert all(item["reason_text"] for item in proposed.json()["deferred"])

    accepted_short = client.post(f"/api/v1/goals/{short_id}/plans/accept", headers=headers)
    assert accepted_short.status_code == 201
    assert "Not enough minutes this time" in accepted_short.json()["rationale"]
    assert "Calling a function" in accepted_short.json()["rationale"]
    assert "insufficient_minutes" not in accepted_short.json()["rationale"]

    overview = client.get(f"/api/v1/goals/{short_id}/overview", headers=headers)
    assert overview.status_code == 200
    _assert_named_payloads(overview.json())

    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names and calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 25,
            },
        },
    )
    goal_id = created.json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    assert accepted.status_code == 201

    questions = [
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    ]
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "to-q",
                "event_type": "progress",
                "payload": {"plan_activity_id": questions[0]["id"]},
            }
        },
    )
    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "once", "choice": "b"},
    )

    progress = client.get("/api/v1/progress", headers=headers)
    assert progress.status_code == 200
    _assert_named_payloads(progress.json())
    assert any(item["facet_label"] == "Shown on your own" for item in progress.json()["facets"])
    assert any(item["facet_label"] == "Not tried yet" for item in progress.json()["unassessed"])

    home = client.get("/api/v1/home", headers=headers)
    assert home.status_code == 200
    _assert_named_payloads(home.json())

    finished = client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers)
    assert finished.status_code == 200
    _assert_named_payloads(finished.json()["summary"])

    reviews = client.get("/api/v1/reviews/due", headers=headers)
    assert reviews.status_code == 200
    _assert_named_payloads(reviews.json())
