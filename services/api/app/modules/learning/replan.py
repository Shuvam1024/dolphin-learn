"""Replan writes a new plan version from remaining study minutes and evidence."""

from app.modules.curriculum.models import Competency
from app.modules.goals.models import Goal, TimeBudget
from app.modules.identity.models import User
from app.modules.learning.accept import save_accepted_version
from app.modules.learning.models import CompetencyState, PlanVersion
from app.modules.learning.planner import PlanProposal, propose_plan
from app.modules.learning.proposals import resolve_domain_key, usable_minutes, work_for_domain
from app.modules.learning.study_time import remaining_minutes, studied_minutes_for_goal
from sqlalchemy import select
from sqlalchemy.orm import Session


def _demonstrated(db: Session, user: User) -> list[str]:
    rows = db.execute(
        select(Competency.key)
        .join(CompetencyState, CompetencyState.competency_id == Competency.id)
        .where(
            CompetencyState.user_id == user.id,
            CompetencyState.status_facet.in_(
                ("independently_demonstrated", "retained", "applied")
            ),
        )
        .order_by(Competency.key)
    ).scalars()
    return list(rows)


def replan_goal(
    db: Session,
    user: User,
    goal: Goal,
    budget: TimeBudget,
) -> tuple[PlanVersion, PlanProposal]:
    demonstrated = _demonstrated(db, user)
    work = [
        item
        for item in work_for_domain(db, resolve_domain_key(db, goal, None))
        if item.key not in set(demonstrated)
    ]
    budget_minutes = usable_minutes(budget)
    studied = studied_minutes_for_goal(db, user, goal)
    left = remaining_minutes(budget_minutes, studied)
    proposal = propose_plan(work, left)
    shown = ", ".join(demonstrated) if demonstrated else "none"
    note = (
        f"Already demonstrated: {shown}. "
        f"Studied minutes: {studied}. Remaining minutes: {left}. "
        "The original budget is unchanged. "
        "Plan proposals still need an explicit accept. This replan wrote a new version."
    )
    version = save_accepted_version(db, user, goal, proposal, note)
    return version, proposal
