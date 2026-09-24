"""Deterministic plan proposal. No model calls.

Prerequisite closure, then a topological order, then a greedy fit against the
minutes the learner actually has. Priority shapes breadth, depth, and a review
reserve. A proposal is not an accepted plan.
"""

from dataclasses import dataclass
from typing import Literal

from app.modules.learning.copy import priority_effect, priority_label

REASON_INSUFFICIENT = "insufficient_minutes"
REASON_PREREQ = "prerequisite_deferred"

Priority = Literal["understand", "apply", "make_it_stick"]
PRIORITIES = frozenset({"understand", "apply", "make_it_stick"})


@dataclass(frozen=True)
class CompetencyWork:
    key: str
    name: str
    effort_low: int
    effort_high: int
    prereq_keys: tuple[str, ...]


@dataclass(frozen=True)
class PlannedCompetency:
    key: str
    name: str
    effort_low: int
    effort_high: int
    position: int
    practice_depth: str = "standard"


@dataclass(frozen=True)
class DeferredCompetency:
    key: str
    name: str
    effort_low: int
    effort_high: int
    reason_code: str


@dataclass(frozen=True)
class PlanProposal:
    usable_minutes: int
    estimated_required_low: int
    estimated_required_high: int
    scope_conflict: bool
    included: tuple[PlannedCompetency, ...]
    deferred: tuple[DeferredCompetency, ...]
    priority: Priority = "understand"
    priority_label: str = "Understand"
    priority_effect: str = ""
    review_reserve_minutes: int = 0
    learning_minutes: int = 0


def normalize_priority(value: str | None) -> Priority:
    if value is None:
        return "understand"
    cleaned = value.strip()
    if cleaned not in PRIORITIES:
        raise ValueError("priority must be understand, apply, or make_it_stick")
    return cleaned  # type: ignore[return-value]


def propose_plan(
    work: list[CompetencyWork],
    usable_minutes: int,
    priority: Priority | str | None = "understand",
) -> PlanProposal:
    if usable_minutes < 0:
        raise ValueError("usable minutes cannot be negative")
    priority_key = normalize_priority(
        priority if isinstance(priority, str) or priority is None else str(priority)
    )
    by_key = {item.key: item for item in work}
    if len(by_key) != len(work):
        raise ValueError("competency keys must be unique")

    required_low = sum(item.effort_low for item in work)
    required_high = sum(item.effort_high for item in work)
    order = _topological(work)
    included: list[PlannedCompetency] = []
    deferred: list[DeferredCompetency] = []
    included_keys: set[str] = set()
    used = 0

    review_reserve = 0
    learning_budget = usable_minutes
    if priority_key == "make_it_stick":
        review_reserve = usable_minutes // 5  # 20%, never more than usable
        learning_budget = usable_minutes - review_reserve

    fit_by_high = priority_key == "apply"
    depth = "full" if fit_by_high else "standard"

    for item in order:
        missing = [key for key in item.prereq_keys if key in by_key and key not in included_keys]
        if missing:
            deferred.append(
                DeferredCompetency(
                    item.key, item.name, item.effort_low, item.effort_high, REASON_PREREQ
                )
            )
            continue
        cost = item.effort_high if fit_by_high else item.effort_low
        if used + cost > learning_budget:
            deferred.append(
                DeferredCompetency(
                    item.key,
                    item.name,
                    item.effort_low,
                    item.effort_high,
                    REASON_INSUFFICIENT,
                )
            )
            continue
        used += cost
        included.append(
            PlannedCompetency(
                item.key,
                item.name,
                item.effort_low,
                item.effort_high,
                len(included) + 1,
                practice_depth=depth,
            )
        )
        included_keys.add(item.key)

    label = priority_label(priority_key)
    effect = priority_effect(priority_key)
    return PlanProposal(
        usable_minutes=usable_minutes,
        estimated_required_low=required_low,
        estimated_required_high=required_high,
        scope_conflict=required_low > usable_minutes,
        included=tuple(included),
        deferred=tuple(deferred),
        priority=priority_key,
        priority_label=label,
        priority_effect=effect,
        review_reserve_minutes=review_reserve,
        learning_minutes=learning_budget,
    )


def _topological(work: list[CompetencyWork]) -> list[CompetencyWork]:
    by_key = {item.key: item for item in work}
    incoming = {item.key: 0 for item in work}
    dependents: dict[str, list[str]] = {item.key: [] for item in work}
    for item in work:
        for prereq in item.prereq_keys:
            if prereq not in by_key:
                continue
            incoming[item.key] += 1
            dependents[prereq].append(item.key)
    ready = sorted(key for key, count in incoming.items() if count == 0)
    ordered: list[CompetencyWork] = []
    while ready:
        key = ready.pop(0)
        ordered.append(by_key[key])
        for child in sorted(dependents[key]):
            incoming[child] -= 1
            if incoming[child] == 0:
                ready.append(child)
                ready.sort()
    if len(ordered) != len(work):
        raise ValueError("competency prerequisites contain a cycle")
    return ordered
