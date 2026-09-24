"""Replan: preview remaining-minute proposals, then accept with a hash."""

from __future__ import annotations

import hashlib
import json

from app.errors import ApiError
from app.modules.curriculum.models import Competency
from app.modules.goals.models import Goal, TimeBudget
from app.modules.identity.models import User
from app.modules.learning.accept import save_accepted_version
from app.modules.learning.models import CompetencyState, LearningPath, PlanVersion
from app.modules.learning.planner import PlanProposal, propose_plan
from app.modules.learning.proposals import resolve_domain_key, usable_minutes, work_for_domain
from app.modules.learning.study_time import remaining_minutes, studied_minutes_for_goal
from sqlalchemy import select
from sqlalchemy.orm import Session


def _demonstrated(db: Session, user: User) -> list[tuple[str, str]]:
    rows = db.execute(
        select(Competency.key, Competency.name)
        .join(CompetencyState, CompetencyState.competency_id == Competency.id)
        .where(
            CompetencyState.user_id == user.id,
            CompetencyState.status_facet.in_(
                ("independently_demonstrated", "retained", "applied")
            ),
        )
        .order_by(Competency.key)
    ).all()
    return [(key, name) for key, name in rows]


def build_replan_proposal(
    db: Session,
    user: User,
    goal: Goal,
    budget: TimeBudget,
) -> tuple[PlanProposal, int, int, list[tuple[str, str]]]:
    from app.modules.learning.proposals import clear_placement_skips

    clear_placement_skips(db, goal)
    demonstrated = _demonstrated(db, user)
    demonstrated_keys = {key for key, _name in demonstrated}
    work = [
        item
        for item in work_for_domain(db, resolve_domain_key(db, goal, None), goal=goal)
        if item.key not in demonstrated_keys
    ]
    budget_minutes = usable_minutes(budget)
    studied = studied_minutes_for_goal(db, user, goal)
    left = remaining_minutes(budget_minutes, studied)
    proposal = propose_plan(work, left, priority=getattr(goal, "priority", None) or "understand")
    return proposal, studied, left, demonstrated


def proposal_hash(proposal: PlanProposal, *, studied: int, left: int) -> str:
    payload = {
        "usable": proposal.usable_minutes,
        "studied": studied,
        "left": left,
        "priority": proposal.priority,
        "included": [item.key for item in proposal.included],
        "deferred": [(item.key, item.reason_code) for item in proposal.deferred],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def accept_replan(
    db: Session,
    user: User,
    goal: Goal,
    budget: TimeBudget,
    *,
    expected_hash: str,
) -> tuple[PlanVersion, PlanProposal]:
    proposal, studied, left, demonstrated = build_replan_proposal(db, user, goal, budget)
    current = proposal_hash(proposal, studied=studied, left=left)
    if current != expected_hash.strip():
        raise ApiError(
            "conflict",
            "This plan preview is out of date. Request a new preview.",
            status_code=409,
        )
    shown = ", ".join(name for _key, name in demonstrated) if demonstrated else "none"
    note = (
        f"Already demonstrated: {shown}. "
        f"Studied minutes: {studied}. Remaining minutes: {left}. "
        "The original budget is unchanged. "
        "Accepted from a replan preview."
    )
    version = save_accepted_version(db, user, goal, proposal, note)
    return version, proposal


def plan_history(db: Session, user: User, goal: Goal) -> list[dict[str, object]]:
    rows = db.scalars(
        select(PlanVersion)
        .join(LearningPath, PlanVersion.learning_path_id == LearningPath.id)
        .where(
            LearningPath.user_id == user.id,
            LearningPath.goal_id == goal.id,
            PlanVersion.status == "accepted",
        )
        .order_by(PlanVersion.version_number.desc())
    ).all()
    return [
        {
            "version_number": row.version_number,
            "usable_minutes": row.usable_minutes or 0,
            "rationale": " ".join(row.rationale.split())[:240],
        }
        for row in rows
    ]


# Back-compat helper used by older call sites during migration.
def replan_goal(
    db: Session,
    user: User,
    goal: Goal,
    budget: TimeBudget,
) -> tuple[PlanVersion, PlanProposal]:
    proposal, studied, left, demonstrated = build_replan_proposal(db, user, goal, budget)
    shown = ", ".join(name for _key, name in demonstrated) if demonstrated else "none"
    note = (
        f"Already demonstrated: {shown}. "
        f"Studied minutes: {studied}. Remaining minutes: {left}. "
        "The original budget is unchanged. "
        "Plan proposals still need an explicit accept. This replan wrote a new version."
    )
    version = save_accepted_version(db, user, goal, proposal, note)
    return version, proposal
