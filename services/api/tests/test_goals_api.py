"""S20: a learner can create, list, and read only their own goals."""

from app.db import SessionLocal
from app.main import app
from app.seed import seed
from fastapi.testclient import TestClient

client = TestClient(app)


def _token(email: str) -> str:
    issued = client.post("/api/v1/dev/token", json={"email": email})
    assert issued.status_code == 200
    return issued.json()["access_token"]


def _headers(email: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(email)}"}


def _seed() -> None:
    with SessionLocal() as db:
        seed(db)


def test_create_list_and_get_own_goal() -> None:
    _seed()
    headers = _headers("s20-owner@example.com")
    created = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "  Learn Python names  ",
            "domain_key": "python",
            "raw_request": "  I want to name values and call functions.  ",
            "normalized_objective": "  Use names and calls  ",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Learn Python names"
    assert body["domain_key"] == "python"
    assert body["raw_request"] == "I want to name values and call functions."
    assert body["normalized_objective"] == "Use names and calls"
    assert body["status"] == "active"
    goal_id = body["id"]

    listed = client.get("/api/v1/goals", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == goal_id for item in listed.json())

    fetched = client.get(f"/api/v1/goals/{goal_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["raw_request"] == body["raw_request"]


def test_other_user_cannot_read_goal() -> None:
    _seed()
    owner = _headers("s20-a@example.com")
    other = _headers("s20-b@example.com")
    created = client.post(
        "/api/v1/goals",
        headers=owner,
        json={
            "title": "Private goal",
            "domain_key": "python",
            "raw_request": "Only A should see this.",
        },
    )
    assert created.status_code == 201
    goal_id = created.json()["id"]

    hidden = client.get(f"/api/v1/goals/{goal_id}", headers=other)
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "not_found"

    others_list = client.get("/api/v1/goals", headers=other)
    assert others_list.status_code == 200
    assert all(item["id"] != goal_id for item in others_list.json())


def test_empty_title_and_request_rejected() -> None:
    _seed()
    headers = _headers("s20-empty@example.com")
    empty_title = client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "   ", "domain_key": "python", "raw_request": "A real request"},
    )
    assert empty_title.status_code == 422
    assert empty_title.json()["error"]["code"] == "validation_error"

    empty_request = client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "A title", "domain_key": "python", "raw_request": " "},
    )
    assert empty_request.status_code == 422
    assert empty_request.json()["error"]["code"] == "validation_error"

    listed = client.get("/api/v1/goals", headers=headers)
    assert listed.status_code == 200
    assert listed.json() == []
