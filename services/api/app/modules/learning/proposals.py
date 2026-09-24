"""Load seeded competencies and propose a plan for one owned goal."""

from __future__ import annotations

from app.errors import ApiError
from app.modules.curriculum.models import EDGE_REQUIRES, Competency, CompetencyEdge, Domain
from app.modules.goals.budget import BudgetMode, TimeBudgetSpec
from app.modules.goals.general import GENERAL_DOMAIN_KEY
from app.modules.goals.models import Goal, TimeBudget
from app.modules.identity.models import User
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


def work_for_domain(
    db: Session,
    domain_key: str,
    *,
    goal: Goal | None = None,
    user: User | None = None,
) -> list[CompetencyWork]:
    from app.modules.learner_model.effort import scale_effort

    domain = db.scalar(select(Domain).where(Domain.key == domain_key))
    if domain is None:
        raise ApiError("validation_error", "Unknown domain", status_code=422)
    query = select(Competency).where(Competency.domain_id == domain.id)
    if domain_key == GENERAL_DOMAIN_KEY:
        if goal is None:
            raise ApiError(
                "validation_error",
                "A Something else goal is required for this subject",
                status_code=422,
            )
        query = query.where(
            Competency.owner_user_id == goal.user_id,
            Competency.goal_id == goal.id,
        )
    else:
        query = query.where(Competency.owner_user_id.is_(None))
    competencies = list(db.scalars(query.order_by(Competency.key)))
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

    learner = user
    if learner is None and goal is not None:
        learner = db.get(User, goal.user_id)

    work: list[CompetencyWork] = []
    for competency in competencies:
        activities = list(
            db.scalars(
                select(ActivityVersion)
                .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
                .where(Lesson.competency_id == competency.id)
            )
        )
        low = 0
        high = 0
        for item in activities:
            scaled_low, scaled_high = scale_effort(
                db,
                learner,
                item.activity_type,
                int(item.effort_minutes_low),
                int(item.effort_minutes_high),
            )
            low += scaled_low
            high += scaled_high
        work.append(
            CompetencyWork(
                key=competency.key,
                name=competency.name,
                effort_low=low,
                effort_high=high,
                prereq_keys=tuple(sorted(prereqs[competency.key])),
            )
        )
    return work


def propose_for_goal(
    db: Session,
    goal: Goal,
    budget: TimeBudget,
    domain_key: str | None,
    *,
    priority: str | None = None,
    skip_competency_keys: list[str] | None = None,
    persist_skips: bool = True,
) -> PlanProposal:
    from app.modules.goals.models import GoalCompetency
    from app.modules.identity.models import User
    from app.modules.learning.planner import DeferredCompetency, REASON_SKIPPED

    resolved = resolve_domain_key(db, goal, domain_key)
    learner = db.get(User, goal.user_id)
    work = work_for_domain(db, resolved, goal=goal, user=learner)
    chosen = priority if priority is not None else getattr(goal, "priority", None) or "understand"

    if skip_competency_keys is not None and persist_skips:
        if skip_competency_keys:
            _persist_skips(db, goal, list(skip_competency_keys))
        else:
            _clear_skips(db, goal)

    if skip_competency_keys is not None:
        active_skips = set(skip_competency_keys)
    else:
        active_skips = {
            key
            for (key,) in db.execute(
                select(Competency.key)
                .join(GoalCompetency, GoalCompetency.competency_id == Competency.id)
                .where(
                    GoalCompetency.goal_id == goal.id,
                    GoalCompetency.requirement == "skipped",
                )
            ).all()
        }

    remaining = [item for item in work if item.key not in active_skips]
    skipped_work = [item for item in work if item.key in active_skips]
    proposal = propose_plan(remaining, usable_minutes(budget), priority=chosen)
    if not skipped_work:
        return proposal
    deferred = list(proposal.deferred) + [
        DeferredCompetency(
            item.key, item.name, item.effort_low, item.effort_high, REASON_SKIPPED
        )
        for item in skipped_work
    ]
    return PlanProposal(
        usable_minutes=proposal.usable_minutes,
        estimated_required_low=proposal.estimated_required_low,
        estimated_required_high=proposal.estimated_required_high,
        scope_conflict=proposal.scope_conflict,
        included=proposal.included,
        deferred=tuple(deferred),
        priority=proposal.priority,
        priority_label=proposal.priority_label,
        priority_effect=proposal.priority_effect,
        review_reserve_minutes=proposal.review_reserve_minutes,
        learning_minutes=proposal.learning_minutes,
    )


def _persist_skips(db: Session, goal: Goal, keys: list[str]) -> None:
    from app.modules.goals.models import GoalCompetency

    _clear_skips(db, goal)
    for key in keys:
        competency = db.scalar(select(Competency).where(Competency.key == key))
        if competency is None:
            continue
        db.add(
            GoalCompetency(
                goal_id=goal.id,
                competency_id=competency.id,
                requirement="skipped",
            )
        )
    db.commit()


def _clear_skips(db: Session, goal: Goal) -> None:
    from app.modules.goals.models import GoalCompetency
    from sqlalchemy import delete

    db.execute(
        delete(GoalCompetency).where(
            GoalCompetency.goal_id == goal.id,
            GoalCompetency.requirement == "skipped",
        )
    )
    db.commit()


def clear_placement_skips(db: Session, goal: Goal) -> None:
    """Replan starts fresh — learner-confirmed skips do not carry over."""
    _clear_skips(db, goal)
