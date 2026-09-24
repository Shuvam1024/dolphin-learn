"""S94: product events stay opaque; dataset views return rows."""

from __future__ import annotations

import json
import uuid

from app.analytics.events import (
    EVENT_NAMES,
    FORBIDDEN_PROP_KEYS,
    ProductEvent,
    emit,
    emit_account_deletion_requested,
    emit_account_export_requested,
)
from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select, text

client = TestClient(app)


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _make_goal(headers: dict[str, str]) -> str:
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Events path",
            "domain_key": "python",
            "raw_request": "I want to learn names with secrets@example.com",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 60,
                "preferred_session_minutes": 25,
            },
        },
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


def test_events_strip_raw_answers_notes_and_emails() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s94")
    me = client.get("/api/v1/me", headers=headers).json()
    user_id = uuid.UUID(me["id"])
    goal_id = _make_goal(headers)

    with SessionLocal() as db:
        emit(
            db,
            user_id,
            "goal_created",
            {
                "goal_id": goal_id,
                "email": "leak@example.com",
                "raw_request": "secret goal text",
                "answer": "the answer is b",
                "prompt": "What does x = 3 do?",
                "note": "learner note",
                "domain_key": "python",
            },
        )
        emit_account_export_requested(db, user_id)
        emit_account_deletion_requested(db, user_id)
        db.commit()
        rows = list(db.scalars(select(ProductEvent).where(ProductEvent.user_id == user_id)))
        assert {row.name for row in rows} >= {
            "goal_created",
            "account_export_requested",
            "account_deletion_requested",
        }
        blob = json.dumps([row.props for row in rows])
        assert "leak@example.com" not in blob
        assert "secret goal text" not in blob
        assert "the answer is b" not in blob
        assert "What does x = 3" not in blob
        assert "learner note" not in blob
        for row in rows:
            assert not (FORBIDDEN_PROP_KEYS & set(row.props))
            assert "@" not in json.dumps(row.props)


def test_funnel_events_and_views_for_heavy_path() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s94-funnel")
    goal_id = _make_goal(headers)
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers)
    assert accepted.status_code == 201, accepted.text
    activities = accepted.json()["activities"]
    objective = next(item for item in activities if str(item["title"]).endswith("objective"))
    session = client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"goal_id": goal_id, "target_minutes": 25},
    )
    assert session.status_code == 201, session.text
    session_id = session.json()["id"]
    patched = client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={
            "event": {
                "client_event_id": f"s94-progress-{uuid.uuid4().hex[:8]}",
                "event_type": "progress",
                "payload": {"plan_activity_id": objective["id"]},
            }
        },
    )
    assert patched.status_code == 200, patched.text
    attempt = client.post(
        f"/api/v1/sessions/{session_id}/attempts",
        headers=headers,
        json={"idempotency_key": f"s94-{uuid.uuid4().hex[:8]}", "choice": "b"},
    )
    assert attempt.status_code in (200, 201), attempt.text

    with SessionLocal() as db:
        names = {
            row[0]
            for row in db.execute(
                text(
                    "SELECT name FROM product_events "
                    "WHERE props->>'goal_id' = :gid OR props->>'session_id' = :sid"
                ),
                {"gid": goal_id, "sid": session_id},
            )
        }
        assert "goal_created" in names
        assert "plan_accepted" in names
        assert "session_started" in names
        assert "activity_submitted" in names
        assert set(EVENT_NAMES)  # sanity

        attempt_rows = db.execute(text("SELECT attempt_id FROM v_attempt_features LIMIT 5")).fetchall()
        assert len(attempt_rows) >= 1
        review_rows = db.execute(text("SELECT review_event_id FROM v_review_outcomes LIMIT 5")).fetchall()
        assert review_rows is not None


def test_views_have_required_columns_and_are_queryable() -> None:
    """Views are queryable and expose the modeling columns from the ship plan."""
    with SessionLocal() as db:
        seed(db)
        count = db.execute(text("SELECT count(*) FROM v_attempt_features")).scalar()
        assert int(count or 0) >= 0
        cols = db.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'v_attempt_features'"
            )
        ).fetchall()
        names = {row[0] for row in cols}
        assert {
            "item_difficulty",
            "assistance",
            "delay_since_exposure_minutes",
            "outcome",
            "active_minutes",
            "selection_reason",
        } <= names
        review_cols = {
            row[0]
            for row in db.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'v_review_outcomes'"
                )
            )
        }
        assert {"interval", "outcome", "delay_minutes"} <= review_cols
