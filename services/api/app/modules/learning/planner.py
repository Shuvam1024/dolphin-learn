"""Deterministic plan proposal. No model calls.

Prerequisite closure, then a topological order, then a greedy fit against the
minutes the learner actually has. Anything that does not fit is deferred with
a reason. A proposal is not an accepted plan.
"""

from dataclasses import dataclass

REASON_INSUFFICIENT = "insufficient_minutes"
REASON_PREREQ = "prerequisite_deferred"


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


def propose_plan(work: list[CompetencyWork], usable_minutes: int) -> PlanProposal:
    if usable_minutes < 0:
        raise ValueError("usable minutes cannot be negative")
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

    for item in order:
        missing = [key for key in item.prereq_keys if key in by_key and key not in included_keys]
        if missing:
            deferred.append(
                DeferredCompetency(
                    item.key, item.name, item.effort_low, item.effort_high, REASON_PREREQ
                )
            )
            continue
        if used + item.effort_low > usable_minutes:
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
        used += item.effort_low
        included.append(
            PlannedCompetency(
                item.key,
                item.name,
                item.effort_low,
                item.effort_high,
                len(included) + 1,
            )
        )
        included_keys.add(item.key)

    return PlanProposal(
        usable_minutes=usable_minutes,
        estimated_required_low=required_low,
        estimated_required_high=required_high,
        scope_conflict=required_low > usable_minutes,
        included=tuple(included),
        deferred=tuple(deferred),
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
