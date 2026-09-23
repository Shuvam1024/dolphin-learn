"""S48: python.conditionals seeds with checks and can fit or defer by minutes."""

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.curriculum.models import Competency, CompetencyEdge
from app.modules.learning.models import ActivityVersion, Lesson
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import func, select

client = TestClient(app)


def test_conditionals_seed_and_plan_scope() -> None:
    with SessionLocal() as db:
        seed(db)
        seed(db)
        assert db.scalar(select(Competency).where(Competency.key == "python.conditionals"))
        lesson = db.scalar(select(Lesson).where(Lesson.key == "python.conditionals.intro"))
        assert lesson is not None
        keyed = db.scalar(
            select(func.count())
            .select_from(ActivityVersion)
            .where(
                ActivityVersion.lesson_id == lesson.id,
                ActivityVersion.answer_key.is_not(None),
            )
        )
        assert keyed is not None and keyed >= 2
        edge = db.scalar(
            select(CompetencyEdge)
            .join(Competency, Competency.id == CompetencyEdge.from_competency_id)
            .where(Competency.key == "python.conditionals")
        )
        assert edge is not None

    headers = {
        "Authorization": (
            "Bearer "
            + client.post(
                "/api/v1/dev/token",
                json={"email": f"s48-{uuid.uuid4().hex[:8]}@example.com"},
            ).json()["access_token"]
        )
    }

    def propose(minutes: int) -> dict[str, object]:
        created = client.post(
            "/api/v1/goals",
            headers=headers,
            json={
                "title": "Python with conditionals",
                "domain_key": "python",
                "raw_request": "Names, calls, and if.",
                "time_budget": {
                    "mode": "one_off",
                    "one_off_minutes": minutes,
                    "preferred_session_minutes": 30,
                },
            },
        )
        assert created.status_code == 201
        body = client.post(
            f"/api/v1/goals/{created.json()['id']}/plan-proposals",
            headers=headers,
            json={},
        )
        assert body.status_code == 200
        return body.json()

    short = propose(15)
    included_short = [item["competency_key"] for item in short["included"]]
    deferred_short = {item["competency_key"]: item["reason_code"] for item in short["deferred"]}
    assert "python.names" in included_short
    assert deferred_short.get("python.conditionals") == "insufficient_minutes"

    long = propose(200)
    included_long = [item["competency_key"] for item in long["included"]]
    assert "python.names" in included_long
    assert "python.conditionals" in included_long
    assert long["scope_conflict"] is False
