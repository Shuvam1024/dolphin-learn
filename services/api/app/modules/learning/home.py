"""Home is the next honest action, not a streak board."""

from app.modules.curriculum.models import Competency
from app.modules.goals.models import Goal
from app.modules.goals.service import list_goals
from app.modules.identity.models import User
from app.modules.learning.accept import latest_accepted
from app.modules.learning.models import CompetencyState, LearningSession
from app.modules.learning.reviews import queue_for_user
from sqlalchemy import select
from sqlalchemy.orm import Session


def _note(db: Session, user: User, goal: Goal) -> str:
    version = latest_accepted(db, user, goal)
    if version is None:
        return "No accepted plan yet."
    return " ".join(version.rationale.split())


def _open_session(db: Session, user: User) -> LearningSession | None:
    return db.scalar(
        select(LearningSession)
        .where(LearningSession.user_id == user.id, LearningSession.status != "finished")
        .order_by(LearningSession.updated_at.desc())
    )


def build_home(db: Session, user: User) -> dict[str, object]:
    goals = list_goals(db, user)
    cards: list[dict[str, str]] = []
    start_goal: Goal | None = None
    for goal in goals:
        cards.append(
            {
                "id": str(goal.id),
                "title": goal.title,
                "feasibility_note": _note(db, user, goal),
            }
        )
        if start_goal is None and latest_accepted(db, user, goal) is not None:
            start_goal = goal

    reviews = queue_for_user(db, user)
    due = [
        {"competency_key": str(item["competency_key"]), "reason": str(item["reason"])}
        for item in reviews["due"]
    ]
    evidence_rows = db.execute(
        select(Competency.key, CompetencyState.status_facet)
        .join(Competency, Competency.id == CompetencyState.competency_id)
        .where(
            CompetencyState.user_id == user.id,
            CompetencyState.status_facet == "independently_demonstrated",
        )
        .order_by(Competency.key)
    ).all()
    evidence = [
        {"competency_key": key, "status_facet": facet} for key, facet in evidence_rows
    ]
    session = _open_session(db, user)
    if due:
        first = due[0]
        action = {
            "kind": "review",
            "title": f"Review {first['competency_key']}",
            "href": "/app/review",
            "goal_id": "",
        }
    elif session is not None:
        action = {
            "kind": "resume_session",
            "title": "Resume your session",
            "href": f"/app/learn/{session.id}",
            "goal_id": "",
        }
    elif start_goal is not None:
        action = {
            "kind": "start_session",
            "title": f"Start a session for {start_goal.title}",
            "href": "",
            "goal_id": str(start_goal.id),
        }
    elif goals:
        action = {
            "kind": "create_goal",
            "title": "Accept a plan before the next session",
            "href": "/app/goals/new",
            "goal_id": "",
        }
    else:
        action = {
            "kind": "create_goal",
            "title": "Create a goal",
            "href": "/app/goals/new",
            "goal_id": "",
        }
    return {
        "next_action": action,
        "goals": cards,
        "due_reviews": due,
        "recent_evidence": evidence,
        "quick_learn": {"href": "/app/goals/new", "label": "Quick Learn"},
    }
