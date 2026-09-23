"""S54: activity versions carry item ids, typed payloads, and provenance."""

from __future__ import annotations

import uuid

import pytest
from alembic import command
from alembic.config import Config
from app.db import SessionLocal, engine
from app.modules.curriculum.models import Competency, Domain
from app.modules.learning.models import ActivityVersion, Lesson
from app.seed import seed
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError


def _alembic_config() -> Config:
    config = Config("alembic.ini")
    return config


def test_activity_types_schema_backfill_and_constraints() -> None:
    with SessionLocal() as db:
        seed(db)
        objective = db.scalar(
            select(ActivityVersion).where(ActivityVersion.activity_type == "objective").limit(1)
        )
        reading = db.scalar(
            select(ActivityVersion).where(ActivityVersion.activity_type == "reading").limit(1)
        )
        assert objective is not None
        assert reading is not None
        assert objective.item_id == f"objective-{objective.version}"
        assert reading.item_id == f"reading-{reading.version}"
        assert objective.payload.get("choices")
        assert {choice["id"] for choice in objective.payload["choices"]} == {"a", "b", "c"}
        assert reading.payload == {} or "choices" not in reading.payload
        assert objective.source == "seed"
        assert objective.provisional is False
        assert objective.reviewed_at is not None

        lesson = db.get(Lesson, objective.lesson_id)
        assert lesson is not None
        assert lesson.source == "seed"
        assert lesson.provisional is False

        bad = ActivityVersion(
            lesson_id=objective.lesson_id,
            version=9001,
            item_id="bad-type-1",
            activity_type="essay",
            prompt="Write anything",
            payload={},
            effort_minutes_low=1,
            effort_minutes_high=2,
        )
        db.add(bad)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        dup = ActivityVersion(
            lesson_id=objective.lesson_id,
            version=9002,
            item_id=objective.item_id,
            activity_type="objective",
            prompt="Duplicate item id",
            payload={"choices": []},
            effort_minutes_low=1,
            effort_minutes_high=2,
        )
        db.add(dup)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        # S62 will enforce: provisional graded items without reviewed_at are not selected.
        # Here we only prove the columns exist so that rule can be written later.
        provisional = ActivityVersion(
            lesson_id=objective.lesson_id,
            version=9003,
            item_id="provisional-objective-1",
            activity_type="short_answer",
            prompt="Name the binding",
            answer_key={"correct": "n"},
            payload={"alternates": ["n"], "normalize": ["strip", "lower"]},
            provisional=True,
            source="ai",
            reviewed_at=None,
            effort_minutes_low=1,
            effort_minutes_high=2,
        )
        db.add(provisional)
        db.commit()
        stored = db.get(ActivityVersion, provisional.id)
        assert stored is not None
        assert stored.provisional is True
        assert stored.reviewed_at is None
        assert stored.activity_type == "short_answer"
        db.delete(stored)
        db.commit()


def test_activity_content_fields_downgrade_restores() -> None:
    """Upgrade then downgrade leaves the old type check and drops new columns."""
    suffix = uuid.uuid4().hex[:8]
    with SessionLocal() as db:
        domain = Domain(key=f"s54-{suffix}", name="S54")
        db.add(domain)
        db.flush()
        skill = Competency(domain_id=domain.id, key=f"s54.skill-{suffix}", name="Skill")
        db.add(skill)
        db.flush()
        lesson = Lesson(
            competency_id=skill.id,
            key=f"s54.lesson-{suffix}",
            title="Lesson",
            body_markdown="Body",
        )
        db.add(lesson)
        db.flush()
        lesson_id = lesson.id
        db.commit()

    config = _alembic_config()
    command.downgrade(config, "0009_goal_domain_key")
    with engine.connect() as conn:
        cols = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'activity_versions'"
                )
            )
        }
        assert "item_id" not in cols
        assert "payload" not in cols
        check = conn.execute(
            text(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname = 'ck_activity_versions_type'"
            )
        ).scalar_one()
        assert "worked_example" not in check
        assert "reading" in check
        # Leave a lesson row so upgrade can run against real data.
        count = conn.execute(
            text("SELECT count(*) FROM lessons WHERE id = :id"),
            {"id": lesson_id},
        ).scalar_one()
        assert int(count) == 1

    command.upgrade(config, "head")
    with SessionLocal() as db:
        seed(db)
        row = db.scalar(select(ActivityVersion).limit(1))
        assert row is not None
        assert row.item_id
        assert isinstance(row.payload, dict)
