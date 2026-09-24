"""S61: worked example sits between reading and the first graded attempt."""

from __future__ import annotations

import uuid

from app.content.loader import errors_only, load_all, validate_all
from app.db import SessionLocal
from app.main import app
from app.modules.learning.models import Attempt
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


def test_loader_inserts_worked_example_after_reading() -> None:
    domains = {item.domain.key: item for item in load_all()}
    python = domains["python"]
    names = next(item for item in python.competencies if item.frontmatter.key == "python.names")
    assert names.worked_example_markdown
    types = [item.type for item in names.items]
    assert "worked_example" in types
    assert types.index("reading") < types.index("worked_example")
    worked = next(item for item in names.items if item.type == "worked_example")
    assert worked.effort_minutes.low == 3
    assert worked.effort_minutes.high == 5


def test_checked_subjects_warn_without_worked_example() -> None:
    # Warning rule fires when markdown section is missing on a checked subject.
    from app.content.rules import validate_domain
    from app.content.schema import (
        CompetencyContent,
        CompetencyFrontmatter,
        ContentItem,
        DomainContent,
        DomainFile,
        EffortMinutes,
    )

    bundle = DomainContent(
        domain=DomainFile(key="python", name="Python"),
        competencies=[
            CompetencyContent(
                path="content/python/fake.md",
                frontmatter=CompetencyFrontmatter(
                    key="python.fake",
                    name="Fake",
                    domain="python",
                    lesson_title="Fake",
                    effort_minutes=EffortMinutes(low=5, high=10),
                    reviewed_by="test",
                    reviewed_on="2026-09-23",
                ),
                reading_markdown=" ".join(["word"] * 100),
                worked_example_markdown=None,
                items=[
                    ContentItem(
                        id="reading-1",
                        type="reading",
                        prompt="Read",
                        effort_minutes=EffortMinutes(low=1, high=2),
                    ),
                    *[
                        ContentItem(
                            id=f"objective-{index}",
                            type="objective",
                            prompt=f"Q{index}?\na) a\nb) b\nc) c",
                            choices=["a", "b", "c"],
                            answer="b",
                            explanation="Because.",
                            misconceptions={"a": "Nope."},
                            difficulty=1,
                            effort_minutes=EffortMinutes(low=1, high=2),
                        )
                        for index in range(2, 5)
                    ],
                ],
            )
        ],
    )
    failures = validate_domain(bundle)
    missing = [
        item
        for item in failures
        if item.rule == "worked_example_missing" and item.severity == "warning"
    ]
    assert missing
    assert errors_only(failures) == []


def test_plan_orders_reading_then_worked_example_then_question() -> None:
    with SessionLocal() as db:
        seed(db)
        db.commit()
    email = f"s61-{uuid.uuid4().hex[:8]}@example.com"
    token = client.post("/api/v1/dev/token", json={"email": email}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/v1/me/adult-acknowledgment", headers=headers, json={})
    goal_id = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Learn Python",
            "domain_key": "python",
            "raw_request": "Names.",
            "time_budget": {
                "mode": "one_off",
                "one_off_minutes": 120,
                "preferred_session_minutes": 30,
            },
        },
    ).json()["id"]
    accepted = client.post(f"/api/v1/goals/{goal_id}/plans/accept", headers=headers).json()
    titles = [item["title"] for item in accepted["activities"][:3]]
    assert titles[0].endswith("reading")
    assert titles[1].endswith("worked_example")
    assert titles[2].endswith("objective")

    session_id = client.post(
        "/api/v1/sessions", headers=headers, json={"goal_id": goal_id}
    ).json()["id"]
    first = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert first["studio_activity"]["activity_type"] == "reading"
    assert first["actions"]["primary"] == "continue"

    client.post(f"/api/v1/sessions/{session_id}/advance", headers=headers)
    second = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert second["studio_activity"]["activity_type"] == "worked_example"
    assert second["actions"]["primary"] == "continue"
    assert "binds" in second["studio_activity"]["body_markdown"].lower() or "n =" in second[
        "studio_activity"
    ]["body_markdown"]

    # Continuing a worked example writes no attempt/evidence.
    client.post(f"/api/v1/sessions/{session_id}/advance", headers=headers)
    with SessionLocal() as db:
        rows = list(
            db.scalars(select(Attempt).where(Attempt.session_id == uuid.UUID(session_id)))
        )
        assert rows == []

    third = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
    assert third["studio_activity"]["activity_type"] == "objective"


def test_current_content_has_no_errors() -> None:
    assert errors_only(validate_all()) == []
