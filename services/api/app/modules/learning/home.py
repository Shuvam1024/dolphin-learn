"""Home is the next honest action, not a streak board."""

from __future__ import annotations

from app.modules.curriculum.models import Competency, Domain
from app.modules.goals.models import Goal
from app.modules.goals.service import list_goals
from app.modules.identity.models import User
from app.modules.learning.accept import activities_for, latest_accepted
from app.modules.learning.copy import facet_label
from app.modules.learning.models import ActivityVersion, CompetencyState, LearningSession, Lesson
from app.modules.learning.reviews import queue_for_user
from app.modules.learning.study_time import remaining_minutes, studied_minutes_for_goal
from sqlalchemy import select
from sqlalchemy.orm import Session


def _open_session(db: Session, user: User) -> LearningSession | None:
    return db.scalar(
        select(LearningSession)
        .where(LearningSession.user_id == user.id, LearningSession.status != "finished")
        .order_by(LearningSession.updated_at.desc())
    )


def _domain_name(db: Session, domain_key: str) -> str:
    domain = db.scalar(select(Domain).where(Domain.key == domain_key))
    return domain.name if domain is not None else domain_key


def _next_lesson_title(db: Session, user: User, goal: Goal) -> str:
    version = latest_accepted(db, user, goal)
    if version is None:
        return ""
    for row in activities_for(db, version):
        if row.activity_version_id is None:
            continue
        activity = db.get(ActivityVersion, row.activity_version_id)
        if activity is None:
            continue
        lesson = db.get(Lesson, activity.lesson_id)
        if lesson is not None:
            return lesson.title
    return ""


def _active_goals(goals: list[Goal]) -> list[Goal]:
    return [goal for goal in goals if goal.status == "active"]


def build_home(db: Session, user: User) -> dict[str, object]:
    goals = list_goals(db, user)
    active = _active_goals(goals)
    cards: list[dict[str, object]] = []
    start_goal: Goal | None = None
    for goal in goals:
        version = latest_accepted(db, user, goal)
        usable = version.usable_minutes if version is not None else 0
        if usable is None:
            usable = 0
        studied = studied_minutes_for_goal(db, user, goal)
        remaining = remaining_minutes(int(usable), studied)
        cards.append(
            {
                "id": str(goal.id),
                "title": goal.title,
                "subject_name": _domain_name(db, goal.domain_key),
                "next_lesson_title": _next_lesson_title(db, user, goal) if version else "",
                "remaining_minutes": remaining,
                "usable_minutes": int(usable),
                "studied_minutes": studied,
                "status": goal.status,
                "feasibility_note": (
                    " ".join(version.rationale.split()) if version is not None else "No accepted plan yet."
                ),
            }
        )
        if start_goal is None and version is not None and goal.status == "active":
            start_goal = goal

    reviews = queue_for_user(db, user)
    due_list = list(reviews["due"])
    due_minutes = sum(int(item.get("estimated_minutes") or 5) for item in due_list) or (
        len(due_list) * 5 if due_list else 0
    )
    first_lesson = ""
    if due_list:
        first_lesson = str(
            due_list[0].get("lesson_title")
            or due_list[0].get("competency_name")
            or due_list[0].get("competency_key")
            or ""
        )
    due_reviews = {
        "count": len(due_list),
        "minutes_estimate": due_minutes,
        "first_lesson_title": first_lesson,
        "items": [
            {
                "competency_key": str(item["competency_key"]),
                "competency_name": str(item.get("competency_name") or item["competency_key"]),
                "reason": str(item["reason"]),
            }
            for item in due_list
        ],
    }

    evidence_rows = db.execute(
        select(Competency.key, Competency.name, CompetencyState.status_facet)
        .join(Competency, Competency.id == CompetencyState.competency_id)
        .where(
            CompetencyState.user_id == user.id,
            CompetencyState.status_facet.in_(("independently_demonstrated", "retained")),
        )
        .order_by(Competency.key)
        .limit(8)
    ).all()
    evidence = [
        {
            "competency_key": key,
            "competency_name": name,
            "facet": facet,
            "status_facet": facet,
            "facet_label": facet_label(facet),
        }
        for key, name, facet in evidence_rows
    ]

    session = _open_session(db, user)
    if due_list:
        first = due_list[0]
        name = str(first.get("competency_name") or first["competency_key"])
        action = {
            "kind": "review",
            "title": f"Review {name}",
            "subtitle": "A delayed check is ready.",
            "minutes_estimate": int(first.get("estimated_minutes") or 5),
            "href": "/app/review",
            "goal_id": "",
        }
    elif session is not None:
        action = {
            "kind": "resume_session",
            "title": "Resume your session",
            "subtitle": "Pick up where you paused.",
            "minutes_estimate": 0,
            "href": f"/app/learn/{session.id}",
            "goal_id": "",
        }
    elif start_goal is not None:
        action = {
            "kind": "start_session",
            "title": f"Continue {start_goal.title}",
            "subtitle": _next_lesson_title(db, user, start_goal) or "Start the next lesson.",
            "minutes_estimate": 25,
            "href": f"/app/goals/{start_goal.id}/start",
            "goal_id": str(start_goal.id),
        }
    elif active:
        action = {
            "kind": "create_goal",
            "title": "Accept a plan before the next session",
            "subtitle": "Your goal needs an accepted plan.",
            "minutes_estimate": 0,
            "href": "/app/goals/new",
            "goal_id": "",
        }
    else:
        action = {
            "kind": "create_goal",
            "title": "Create a goal",
            "subtitle": "Tell Dolphin what you want to learn.",
            "minutes_estimate": 0,
            "href": "/app/goals/new",
            "goal_id": "",
        }
    return {
        "next_action": action,
        "goals": cards,
        "due_reviews": due_reviews,
        "recent_evidence": evidence,
        "quick_learn": {"href": "/app/goals/new", "label": "Quick Learn"},
    }
