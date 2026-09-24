"""S92: Difficulty- and history-aware item selection."""

from __future__ import annotations

import uuid

from app.db import SessionLocal
from app.main import app
from app.modules.curriculum.models import Competency
from app.modules.identity.models import User
from app.modules.learning.item_pool import pick_next
from app.modules.learning.models import (
    ActivityVersion,
    Attempt,
    Evaluation,
    LearningSession,
    Lesson,
    SessionEvent,
)
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

client = TestClient(app)


def _headers(prefix: str) -> dict[str, str]:
    issued = client.post(
        "/api/v1/dev/token",
        json={"email": f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"},
    )
    return {"Authorization": f"Bearer {issued.json()['access_token']}"}


def _user_and_competency(headers: dict[str, str]) -> tuple[User, uuid.UUID]:
    me = client.get("/api/v1/me", headers=headers).json()
    with SessionLocal() as db:
        seed(db)
        user = db.get(User, uuid.UUID(me["id"]))
        assert user is not None
        competency = db.scalar(select(Competency).where(Competency.key == "python.names"))
        assert competency is not None
        db.expunge(user)
        return user, competency.id


def test_pick_next_table_over_histories() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s92")
    user, competency_id = _user_and_competency(headers)

    with SessionLocal() as db:
        user = db.merge(user)
        first = pick_next(db, user, competency_id, purpose="first")
        assert first is not None
        assert first.selection_reason == "first_easy"
        assert (first.activity.difficulty or 2) <= 2

        # Independent correct → step up on fresh check
        attempt = Attempt(
            user_id=user.id,
            activity_version_id=first.activity.id,
            response={"choice": "b", "assistance": "none"},
        )
        db.add(attempt)
        db.flush()
        db.add(
            Evaluation(
                attempt_id=attempt.id,
                score=1,
                assistance="none",
                outcome="correct",
                evaluator="test",
            )
        )
        db.commit()

        stepped = pick_next(
            db, user, competency_id, purpose="fresh_check", exclude_ids={first.activity.id}
        )
        assert stepped is not None
        assert "step_up" in stepped.selection_reason
        assert stepped.activity.id != first.activity.id


def test_pick_next_never_returns_revealed_solution() -> None:
    with SessionLocal() as db:
        seed(db)
    headers = _headers("s92-rev")
    user, competency_id = _user_and_competency(headers)

    with SessionLocal() as db:
        user = db.merge(user)
        activities = list(
            db.scalars(
                select(ActivityVersion)
                .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
                .where(
                    Lesson.competency_id == competency_id,
                    ActivityVersion.activity_type == "objective",
                    ActivityVersion.provisional.is_(False),
                )
            )
        )
        assert len(activities) >= 2
        revealed = activities[0]
        session = LearningSession(user_id=user.id, status="active")
        db.add(session)
        db.flush()
        db.add(
            SessionEvent(
                session_id=session.id,
                client_event_id="sol-1",
                event_type="solution",
                payload={"activity_version_id": str(revealed.id)},
            )
        )
        db.commit()

        for purpose in ("first", "fresh_check", "review", "retry"):
            picked = pick_next(db, user, competency_id, purpose=purpose)  # type: ignore[arg-type]
            assert picked is not None
            assert picked.activity.id != revealed.id
