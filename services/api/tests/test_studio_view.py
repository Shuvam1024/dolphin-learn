"""S57: studio actions table and ownership for the session payload."""

from __future__ import annotations

import uuid

import pytest
from app.db import SessionLocal
from app.main import app
from app.modules.learning.studio_view import compute_actions
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.mark.parametrize(
    ("kwargs", "primary"),
    [
        (
            {
                "activity_type": "reading",
                "recorded": False,
                "outcome": "",
                "assistance": "",
                "help_kind": "none",
                "tutor_enabled": True,
                "challenge": False,
                "is_last": False,
            },
            "continue",
        ),
        (
            {
                "activity_type": "objective",
                "recorded": False,
                "outcome": "",
                "assistance": "",
                "help_kind": "none",
                "tutor_enabled": True,
                "challenge": False,
                "is_last": False,
            },
            "submit",
        ),
        (
            {
                "activity_type": "objective",
                "recorded": True,
                "outcome": "correct",
                "assistance": "independent",
                "help_kind": "none",
                "tutor_enabled": True,
                "challenge": False,
                "is_last": False,
            },
            "continue",
        ),
        (
            {
                "activity_type": "objective",
                "recorded": True,
                "outcome": "correct",
                "assistance": "assisted",
                "help_kind": "solution",
                "tutor_enabled": True,
                "challenge": False,
                "is_last": False,
            },
            "fresh_check",
        ),
        (
            {
                "activity_type": "objective",
                "recorded": True,
                "outcome": "incorrect",
                "assistance": "independent",
                "help_kind": "none",
                "tutor_enabled": True,
                "challenge": False,
                "is_last": False,
            },
            "continue",
        ),
        (
            {
                "activity_type": "objective",
                "recorded": False,
                "outcome": "",
                "assistance": "",
                "help_kind": "none",
                "tutor_enabled": True,
                "challenge": True,
                "is_last": False,
            },
            "submit",
        ),
        (
            {
                "activity_type": "objective",
                "recorded": False,
                "outcome": "",
                "assistance": "",
                "help_kind": "none",
                "tutor_enabled": False,
                "challenge": False,
                "is_last": False,
            },
            "submit",
        ),
    ],
)
def test_compute_actions_table(kwargs: dict[str, object], primary: str) -> None:
    actions = compute_actions(**kwargs)  # type: ignore[arg-type]
    assert actions["primary"] == primary
    if kwargs["challenge"]:
        assert actions["can_reveal"] is False
    if not kwargs["tutor_enabled"]:
        assert actions["can_explain_differently"] is False
    else:
        assert actions["can_explain_differently"] is True


def test_studio_payload_hides_explanation_before_attempt_and_ownership() -> None:
    with SessionLocal() as db:
        seed(db)
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"s57-{uuid.uuid4().hex[:8]}@example.com"},
    )
    headers = {"Authorization": f"Bearer {issued.json()['access_token']}"}
    other = client.post(
        "/api/v1/dev/token",
        json={"email": f"s57-other-{uuid.uuid4().hex[:8]}@example.com"},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 25,
            },
        },
    )
    goal_id = created.json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    question = next(
        item for item in accepted.json()["activities"] if item["title"].endswith("objective")
    )
    started = client.post("/api/v1/sessions", headers=headers, json={"goal_id": goal_id})
    session_id = started.json()["id"]
    assert started.json()["actions"]["primary"] == "continue"
    assert started.json()["studio_activity"]["state"]["explanation"] == ""

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
    before = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert before.status_code == 200
    body = before.json()
    assert body["actions"]["primary"] == "submit"
    assert body["studio_activity"]["state"]["explanation"] == ""
    assert body["studio_activity"]["state"]["recorded"] is False
    assert body["lesson"]["competency_name"]
    assert body["remaining_estimate"]["low"] >= 0

    client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": "once", "choice": "b"},
    )
    after = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert after.json()["studio_activity"]["state"]["recorded"] is True
    assert after.json()["studio_activity"]["state"]["explanation"]

    denied = client.get(f"/api/v1/sessions/{session_id}", headers=other_headers)
    assert denied.status_code == 404
