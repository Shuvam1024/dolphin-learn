"""Optional diagnostic sample. Answers are stored. Mastery is not awarded."""

import uuid

from app.errors import ApiError
from app.modules.curriculum.models import Competency, Domain
from app.modules.goals.models import DiagnosticRun, Goal
from app.modules.identity.models import User
from app.modules.learning.models import ActivityVersion, Attempt, Lesson
from sqlalchemy import select
from sqlalchemy.orm import Session

NOTE = "This sample does not claim mastery."


def items_for_goal(db: Session, goal: Goal) -> list[ActivityVersion]:
    text = f"{goal.title} {goal.raw_request}".lower()
    domain_key = "math" if "math" in text or "fraction" in text else "python"
    rows = db.scalars(
        select(ActivityVersion)
        .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
        .join(Competency, Lesson.competency_id == Competency.id)
        .join(Domain, Competency.domain_id == Domain.id)
        .where(Domain.key == domain_key, ActivityVersion.activity_type == "objective")
        .order_by(ActivityVersion.version, ActivityVersion.id)
    )
    return list(rows)[:8]


def start_diagnostic(db: Session, goal: Goal) -> list[ActivityVersion]:
    items = items_for_goal(db, goal)
    if not 3 <= len(items) <= 8:
        raise ApiError(
            "validation_error",
            "A diagnostic needs between 3 and 8 seeded questions",
            status_code=422,
        )
    return items


def skip_diagnostic(db: Session, user: User, goal: Goal) -> DiagnosticRun:
    run = DiagnosticRun(
        user_id=user.id,
        goal_id=goal.id,
        status="skipped",
        answered_count=0,
        mastery_claimed=False,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def submit_diagnostic(
    db: Session,
    user: User,
    goal: Goal,
    answers: list[tuple[uuid.UUID, str]],
) -> tuple[DiagnosticRun, list[Attempt]]:
    if not answers or len(answers) > 8:
        raise ApiError(
            "validation_error",
            "Submit between 1 and 8 answers. You can submit the rest later.",
            status_code=422,
        )
    allowed = {item.id for item in items_for_goal(db, goal)}
    attempts: list[Attempt] = []
    for activity_id, choice in answers:
        if activity_id not in allowed:
            raise ApiError(
                "validation_error",
                "That question is not part of this diagnostic",
                status_code=422,
            )
        attempt = Attempt(
            user_id=user.id,
            activity_version_id=activity_id,
            response={"choice": choice, "source": "diagnostic"},
        )
        db.add(attempt)
        attempts.append(attempt)
    run = DiagnosticRun(
        user_id=user.id,
        goal_id=goal.id,
        status="recorded",
        answered_count=len(answers),
        mastery_claimed=False,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    for attempt in attempts:
        db.refresh(attempt)
    return run, attempts
