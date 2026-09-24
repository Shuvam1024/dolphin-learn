"""S64: short-answer and numeric grading."""

from __future__ import annotations

from decimal import Decimal

from app.modules.learning.grading import (
    grade_numeric,
    grade_short_answer,
    normalize_text,
    parse_number,
)
from app.modules.learning.models import ActivityVersion


def _short(answer: str, alternates: list[str] | None = None) -> ActivityVersion:
    return ActivityVersion(
        lesson_id=__import__("uuid").uuid4(),
        version=1,
        item_id="sa",
        activity_type="short_answer",
        prompt="q",
        answer_key={"correct": answer},
        payload={"alternates": alternates or []},
        effort_minutes_low=1,
        effort_minutes_high=2,
    )


def _numeric(answer: str, tolerance: float = 0.0) -> ActivityVersion:
    return ActivityVersion(
        lesson_id=__import__("uuid").uuid4(),
        version=1,
        item_id="num",
        activity_type="numeric",
        prompt="q",
        answer_key={"correct": answer},
        payload={"tolerance": tolerance, "accept_fractions": True},
        effort_minutes_low=1,
        effort_minutes_high=2,
    )


def test_normalize_and_alternates() -> None:
    assert normalize_text("  Binds the Name to a Value. ") == "binds the name to a value"
    activity = _short("binds the name to a value", ["binds a name to a value"])
    assert grade_short_answer(activity, "Binds a name to a value!").outcome == "correct"
    assert grade_short_answer(activity, "locks a box").outcome == "incorrect"
    assert grade_short_answer(activity, "").outcome == "incorrect"


def test_numeric_forms_and_tolerance() -> None:
    activity = _numeric("0.75", tolerance=0.01)
    for raw in ("0.75", "3/4", ".75", "0.750"):
        assert grade_numeric(activity, raw).outcome == "correct", raw
    assert grade_numeric(activity, "0.7").outcome == "incorrect"
    assert grade_numeric(activity, "").outcome == "incorrect"
    assert parse_number("1 1/2") == Decimal("1.5")
    assert parse_number("1,000") == Decimal("1000")
