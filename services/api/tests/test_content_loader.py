"""S55: content files load, rules fail with path+line, seed is idempotent."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.content.loader import errors_only, load_all, load_domain, validate_all
from app.content.rules import validate_domain
from app.db import SessionLocal
from app.modules.learning.models import ActivityVersion, Lesson
from app.seed import seed
from sqlalchemy import func, select

FIXTURES = Path(__file__).parent / "fixtures" / "content_bad"


def test_current_content_loads_and_validates() -> None:
    domains = load_all()
    assert {item.domain.key for item in domains} >= {"python", "math", "software"}
    failures = validate_all()
    assert errors_only(failures) == []


@pytest.mark.parametrize(
    ("folder", "rule"),
    [
        ("dup_ids", "unique_ids"),
        ("missing_requires", "requires_exist"),
        ("cycle", "no_cycles"),
        ("few_graded", "graded_count"),
        ("no_explanation", "explanation_required"),
        ("short_reading", "reading_length"),
        ("answer_in_prompt", "prompt_hides_answer"),
        ("no_difficulty", "difficulty_present"),
        ("bad_effort", "effort_realistic"),
    ],
)
def test_each_rule_has_failing_fixture(folder: str, rule: str) -> None:
    bundle = load_domain(FIXTURES / folder)
    failures = validate_domain(bundle)
    matched = [item for item in failures if item.rule == rule]
    assert matched, failures
    assert matched[0].path
    assert matched[0].line >= 1


def test_seed_twice_is_idempotent() -> None:
    with SessionLocal() as db:
        seed(db)
        first_lessons = db.scalar(select(func.count()).select_from(Lesson))
        first_activities = db.scalar(select(func.count()).select_from(ActivityVersion))
        seed(db)
        second_lessons = db.scalar(select(func.count()).select_from(Lesson))
        second_activities = db.scalar(select(func.count()).select_from(ActivityVersion))
        assert first_lessons == second_lessons
        assert first_activities == second_activities
        explained = db.scalars(
            select(ActivityVersion).where(ActivityVersion.activity_type == "objective")
        ).all()
        assert explained
        assert all(item.explanation for item in explained)
        assert all(item.source == "seed" for item in explained)
        assert all(item.reviewed_at is not None for item in explained)
