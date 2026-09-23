"""Load seeded competencies and propose a plan for one owned goal."""

from app.errors import ApiError
from app.modules.curriculum.models import EDGE_REQUIRES, Competency, CompetencyEdge, Domain
from app.modules.goals.budget import BudgetMode, TimeBudgetSpec
from app.modules.goals.models import Goal, TimeBudget
from app.modules.learning.models import ActivityVersion, Lesson
from app.modules.learning.planner import CompetencyWork, PlanProposal, propose_plan
from sqlalchemy import select
from sqlalchemy.orm import Session


def usable_minutes(budget: TimeBudget) -> int:
    mode: BudgetMode = "one_off" if budget.mode == "one_off" else "weekly"
    spec = TimeBudgetSpec(
        mode=mode,
        one_off_minutes=budget.one_off_minutes,
        weekly_minutes_per_day=budget.weekly_minutes_per_day,
        horizon_days=budget.horizon_days,
        preferred_session_minutes=budget.preferred_session_minutes,
    )
    if spec.mode == "one_off":
        assert spec.one_off_minutes is not None
        return spec.one_off_minutes
    assert spec.weekly_minutes_per_day is not None and spec.horizon_days is not None
    return spec.weekly_minutes_per_day * spec.horizon_days


def resolve_domain_key(db: Session, goal: Goal, override: str | None) -> str:
    """Use the goal’s domain, or an explicit override. Never guess from the title."""
    key = (override or goal.domain_key or "").strip()
    if not key:
        raise ApiError(
            "validation_error",
            "Choose a subject before asking for a plan",
            status_code=422,
        )
    domain = db.scalar(select(Domain).where(Domain.key == key))
    if domain is None:
        raise ApiError(
            "validation_error",
            "We do not have lessons for that subject yet",
            status_code=422,
        )
    return domain.key


def work_for_domain(db: Session, domain_key: str) -> list[CompetencyWork]:
    domain = db.scalar(select(Domain).where(Domain.key == domain_key))
    if domain is None:
        raise ApiError("validation_error", "Unknown domain", status_code=422)
    competencies = list(
        db.scalars(
            select(Competency).where(Competency.domain_id == domain.id).order_by(Competency.key)
        )
    )
    ids = {item.id: item for item in competencies}
    prereqs: dict[str, list[str]] = {item.key: [] for item in competencies}
    if ids:
        edges = db.scalars(
            select(CompetencyEdge).where(
                CompetencyEdge.edge_type == EDGE_REQUIRES,
                CompetencyEdge.from_competency_id.in_(ids),
            )
        )
        for edge in edges:
            source = ids.get(edge.from_competency_id)
            target = ids.get(edge.to_competency_id)
            if source is None or target is None:
                continue
            prereqs[source.key].append(target.key)

    work: list[CompetencyWork] = []
    for competency in competencies:
        activities = list(
            db.scalars(
                select(ActivityVersion)
                .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
                .where(Lesson.competency_id == competency.id)
            )
        )
        work.append(
            CompetencyWork(
                key=competency.key,
                name=competency.name,
                effort_low=sum(item.effort_minutes_low for item in activities),
                effort_high=sum(item.effort_minutes_high for item in activities),
                prereq_keys=tuple(sorted(prereqs[competency.key])),
            )
        )
    return work


def propose_for_goal(
    db: Session,
    goal: Goal,
    budget: TimeBudget,
    domain_key: str | None,
) -> PlanProposal:
    work = work_for_domain(db, resolve_domain_key(db, goal, domain_key))
    return propose_plan(work, usable_minutes(budget))
