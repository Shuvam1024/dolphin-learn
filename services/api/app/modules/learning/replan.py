"""Replan writes a new plan version from the current budget and evidence."""

from app.modules.curriculum.models import Competency
from app.modules.goals.models import Goal, TimeBudget
from app.modules.identity.models import User
from app.modules.learning.accept import save_accepted_version
from app.modules.learning.models import CompetencyState, PlanVersion
from app.modules.learning.planner import PlanProposal, propose_plan
from app.modules.learning.proposals import domain_key_for, usable_minutes, work_for_domain
from sqlalchemy import select
from sqlalchemy.orm import Session


def _demonstrated(db: Session, user: User) -> list[str]:
    rows = db.execute(
        select(Competency.key)
        .join(CompetencyState, CompetencyState.competency_id == Competency.id)
        .where(
            CompetencyState.user_id == user.id,
            CompetencyState.status_facet == "independently_demonstrated",
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
        for item in work_for_domain(db, domain_key_for(goal, None))
        if item.key not in set(demonstrated)
    ]
    proposal = propose_plan(work, usable_minutes(budget))
    shown = ", ".join(demonstrated) if demonstrated else "none"
    note = (
        f"Already demonstrated: {shown}. "
        "Plan proposals still need an explicit accept. This replan wrote a new version."
    )
    version = save_accepted_version(db, user, goal, proposal, note)
    return version, proposal
