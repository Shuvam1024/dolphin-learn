"""S60: feedback view fills explanation and misconception notes after attempts."""

from __future__ import annotations

import uuid

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _token(email: str) -> dict[str, str]:
    token = client.post("/api/v1/dev/token", json={"email": email}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/v1/me/adult-acknowledgment", headers=headers, json={})
    return headers


def _session_on_objective(headers: dict[str, str]) -> tuple[str, str]:
    with SessionLocal() as db:
        seed(db)
        db.commit()
    goal_id = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names and calls.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 30,
            },
        },
    ).json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers).json()
    question = next(item for item in accepted["activities"] if item["title"].endswith("objective"))
    session_id = client.post(
        "/api/v1/sessions", headers=headers, json={"goal_id": goal_id}
    ).json()["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": "to-q",
                "event_type": "progress",
                "payload": {"plan_activity_id": question["id"]},
            }
        },
    )
    return session_id, question["id"]


def test_wrong_choice_fills_misconception_and_explanation() -> None:
    headers = _token(f"s60-wrong-{uuid.uuid4().hex[:8]}@example.com")
    session_id, _ = _session_on_objective(headers)
    before = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert before["studio_activity"]["state"]["explanation"] == ""
    assert before["studio_activity"]["state"]["misconception_note"] == ""

    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "wrong", "choice": "a"},
    )
    after = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    state = after["studio_activity"]["state"]
    assert state["recorded"] is True
    assert state["response"] == "a"
    assert state["outcome"] == "incorrect"
    assert state["explanation"]
    note = state["misconception_note"].lower()
    assert note
    assert "rebound" in note or "name" in note or "box" in note
    assert after["actions"]["primary"] == "continue"


def test_assisted_answer_primary_is_fresh_check() -> None:
    headers = _token(f"s60-assist-{uuid.uuid4().hex[:8]}@example.com")
    session_id, _ = _session_on_objective(headers)
    client.post(f"/api/v1/sessions/{session_id}/solution", headers=headers, json={"mode": "guided"})
    revealed = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert revealed["studio_activity"]["state"]["revealed_answer"]
    assert revealed["studio_activity"]["state"]["explanation"]

    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "after-sol", "choice": "b"},
    )
    after = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert after["studio_activity"]["state"]["assistance"] == "assisted"
    assert after["actions"]["primary"] == "fresh_check"


def test_summary_collects_watch_out_for() -> None:
    headers = _token(f"s60-sum-{uuid.uuid4().hex[:8]}@example.com")
    session_id, _ = _session_on_objective(headers)
    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "bad", "choice": "a"},
    )
    finished = client.post(f"/api/v1/sessions/{session_id}/finish", headers=headers).json()
    summary = finished.get("summary") or client.get(
        f"/api/v1/sessions/{session_id}", headers=headers
    ).json()["summary"]
    assert summary is not None
    assert "watch_out_for" in summary
    assert summary["watch_out_for"]
    assert "congrat" not in summary["note"].lower()
    assert "great job" not in summary["note"].lower()
