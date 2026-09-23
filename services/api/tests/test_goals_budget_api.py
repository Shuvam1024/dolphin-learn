"""S21: time budgets are stored only when the mode rules hold."""

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _headers(email: str) -> dict[str, str]:
    issued = client.post("/api/v1/dev/token", json={"email": email})
    assert issued.status_code == 200
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def test_rejects_negative_minutes_and_double_counted_modes() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s21-bad@example.com")
    negative = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Too small",
            "domain_key": "python",
            "raw_request": "Learn Python",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": -10,
                "preferred_session_minutes": 25,
            },
        },
    )
    assert negative.status_code == 422
    assert negative.json()["error"]["code"] == "validation_error"

    both = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Both modes",
            "domain_key": "python",
            "raw_request": "Learn Python",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "weekly_minutes_per_day": 30,
                "horizon_days": 14,
                "preferred_session_minutes": 25,
            },
        },
    )
    assert both.status_code == 422
    assert both.json()["error"]["code"] == "validation_error"

    listed = client.get("/api/v1/goals", headers=headers)
    assert listed.json() == []


def test_accepts_quick_learn_and_two_week_window() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s21-ok@example.com")
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Quick Learn Python",
            "domain_key": "python",
            "raw_request": "I have two hours today.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 30,
            },
        },
    )
    assert created.status_code == 201
    budget = created.json()["time_budget"]
    assert budget["mode"] == "one_off"
    assert budget["one_off_minutes"] == 120
    assert budget["weekly_minutes_per_day"] is None
    goal_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/goals/{goal_id}",
        headers=headers,
        json={
            "time_budget": {
                "mode": "weekly",
                "weekly_minutes_per_day": 30,
                "horizon_days": 14,
                "preferred_session_minutes": 30,
            }
        },
    )
    assert updated.status_code == 200
    weekly = updated.json()["time_budget"]
    assert weekly["mode"] == "weekly"
    assert weekly["weekly_minutes_per_day"] == 30
    assert weekly["horizon_days"] == 14
    assert weekly["one_off_minutes"] is None

    fetched = client.get(f"/api/v1/goals/{goal_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["time_budget"]["horizon_days"] == 14
