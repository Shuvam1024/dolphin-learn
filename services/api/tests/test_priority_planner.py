"""S71: priority enum shapes breadth, depth, and review reserve."""

from __future__ import annotations

from app.modules.learning.accept import rationale_for
from app.modules.learning.planner import (
    REASON_PREREQ,
    CompetencyWork,
    propose_plan,
)


def _chain() -> list[CompetencyWork]:
    return [
        CompetencyWork("a", "Alpha", 10, 20, ()),
        CompetencyWork("b", "Bravo", 10, 20, ("a",)),
        CompetencyWork("c", "Charlie", 10, 20, ("b",)),
        CompetencyWork("d", "Delta", 10, 20, ("c",)),
        CompetencyWork("e", "Echo", 10, 20, ("d",)),
    ]


def test_prerequisites_never_violated() -> None:
    plan = propose_plan(_chain(), 25, priority="understand")
    keys = [item.key for item in plan.included]
    assert keys == ["a", "b"]
    for item in plan.included:
        work = next(w for w in _chain() if w.key == item.key)
        for prereq in work.prereq_keys:
            assert prereq in keys
    deferred_prereq = [item for item in plan.deferred if item.reason_code == REASON_PREREQ]
    assert deferred_prereq  # later topics wait on deferred parents


def test_understand_fits_at_least_as_many_as_apply() -> None:
    minutes = 45
    understand = propose_plan(_chain(), minutes, priority="understand")
    apply = propose_plan(_chain(), minutes, priority="apply")
    assert len(understand.included) >= len(apply.included)
    assert all(item.practice_depth == "standard" for item in understand.included)
    assert all(item.practice_depth == "full" for item in apply.included)


def test_make_it_stick_reserve_never_exceeds_usable() -> None:
    for usable in (0, 5, 20, 100, 419):
        plan = propose_plan(_chain(), usable, priority="make_it_stick")
        assert 0 <= plan.review_reserve_minutes <= usable
        assert plan.learning_minutes == usable - plan.review_reserve_minutes
        assert plan.review_reserve_minutes == usable // 5
        used = sum(
            next(w for w in _chain() if w.key == item.key).effort_low for item in plan.included
        )
        assert used <= plan.learning_minutes


def test_rationale_has_priority_label_not_raw_enum() -> None:
    plan = propose_plan(_chain(), 40, priority="make_it_stick")
    text = rationale_for(plan)
    assert "Make it stick" in text
    assert "make_it_stick" not in text
    assert "Focus:" in text
    assert "Review reserve:" in text
