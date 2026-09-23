"""Goal path: ordered activities, deferred topics, and the session to continue."""

from app.errors import ApiError
from app.modules.curriculum.models import Competency
from app.modules.goals.models import Goal
from app.modules.goals.service import budget_for
from app.modules.identity.models import User
from app.modules.learning.accept import activities_for, latest_accepted
from app.modules.learning.models import (
    ActivityVersion,
    CompetencyState,
    LearningSession,
    Lesson,
    PlanActivity,
)
from app.modules.learning.proposals import domain_key_for, propose_for_goal, work_for_domain
from sqlalchemy import select
from sqlalchemy.orm import Session


def _competency_key(db: Session, activity: PlanActivity) -> str:
    if activity.activity_version_id is None:
        return ""
    version = db.get(ActivityVersion, activity.activity_version_id)
    if version is None:
        return ""
    lesson = db.get(Lesson, version.lesson_id)
    if lesson is None:
        return ""
    competency = db.get(Competency, lesson.competency_id)
    return competency.key if competency is not None else ""


def build_overview(db: Session, user: User, goal: Goal) -> dict[str, object]:
    version = latest_accepted(db, user, goal)
    if version is None:
        raise ApiError("not_found", "No accepted plan", status_code=404)
    budget = budget_for(db, goal)
    deferred: list[dict[str, str]] = []
    if budget is not None:
        proposal = propose_for_goal(db, goal, budget, None)
        deferred = [
            {"competency_key": item.key, "reason_code": item.reason_code}
            for item in proposal.deferred
        ]
    facets = {
        key: facet
        for key, facet in db.execute(
            select(Competency.key, CompetencyState.status_facet)
            .join(Competency, Competency.id == CompetencyState.competency_id)
            .where(CompetencyState.user_id == user.id)
        ).all()
    }
    prereq_keys = {
        key
        for item in work_for_domain(db, domain_key_for(goal, None))
        for key in item.prereq_keys
    }
    activities: list[dict[str, object]] = []
    for row in activities_for(db, version):
        key = _competency_key(db, row)
        facet = facets.get(key, "")
        if facet == "independently_demonstrated":
            label = "demonstrated"
        elif key in prereq_keys:
            label = "prereq"
        else:
            label = "included"
        activities.append(
            {
                "id": str(row.id),
                "position": row.position,
                "title": row.title,
                "label": label,
                "competency_key": key,
            }
        )
    pending = next((item for item in activities if item["label"] != "demonstrated"), None)
    if pending is None:
        why = "Why this next? Every activity on this plan is already independently demonstrated."
    elif pending["label"] == "prereq":
        why = f"Why this next? {pending['title']} is a prerequisite for a later topic."
    else:
        why = (
            f"Why this next? {pending['title']} is the next unfinished "
            "activity on the accepted plan."
        )
    session = db.scalar(
        select(LearningSession)
        .join(PlanActivity, LearningSession.plan_activity_id == PlanActivity.id)
        .where(
            LearningSession.user_id == user.id,
            LearningSession.status != "finished",
            PlanActivity.plan_version_id == version.id,
        )
        .order_by(LearningSession.updated_at.desc())
    )
    if session is None:
        continue_action = {"kind": "start", "href": "", "goal_id": str(goal.id)}
    else:
        continue_action = {
            "kind": "resume",
            "href": f"/app/learn/{session.id}",
            "goal_id": str(goal.id),
        }
    return {
        "goal_id": str(goal.id),
        "title": goal.title,
        "version_number": version.version_number,
        "feasibility_note": " ".join(version.rationale.split()),
        "why_next": why,
        "continue_action": continue_action,
        "activities": activities,
        "deferred": deferred,
    }
