"""Optional diagnostic sample. Answers are stored. Mastery is not awarded."""

import uuid

from app.errors import ApiError
from app.modules.curriculum.models import Competency, Domain
from app.modules.goals.general import GENERAL_DOMAIN_KEY
from app.modules.goals.models import DiagnosticRun, Goal
from app.modules.identity.models import User
from app.modules.learning.item_pool import pick_unseen
from app.modules.learning.models import ActivityVersion, Attempt, Lesson
from sqlalchemy import select
from sqlalchemy.orm import Session

NOTE = "This sample does not claim mastery."


def start_diagnostic(db: Session, user: User, goal: Goal) -> list[ActivityVersion]:
    if goal.domain_key == GENERAL_DOMAIN_KEY:
        raise ApiError(
            "validation_error",
            "Placement is not available for Something else",
            status_code=422,
        )
    if not goal.domain_key:
        raise ApiError(
            "validation_error",
            "Choose a subject before starting a diagnostic",
            status_code=422,
        )
    competencies = list(
        db.scalars(
            select(Competency)
            .join(Domain, Competency.domain_id == Domain.id)
            .where(Domain.key == goal.domain_key, Competency.owner_user_id.is_(None))
            .order_by(Competency.key)
        )
    )
    items: list[ActivityVersion] = []
    for competency in competencies:
        result = pick_unseen(
            db,
            user,
            competency.id,
            graded=True,
            activity_types=("objective",),
        )
        if result is None:
            continue
        items.append(result.activity)
        if len(items) >= 5:
            break
    if len(items) < 3:
        rows = list(
            db.scalars(
                select(ActivityVersion)
                .join(Lesson, ActivityVersion.lesson_id == Lesson.id)
                .join(Competency, Lesson.competency_id == Competency.id)
                .join(Domain, Competency.domain_id == Domain.id)
                .where(
                    Domain.key == goal.domain_key,
                    ActivityVersion.activity_type == "objective",
                    Competency.owner_user_id.is_(None),
                    ActivityVersion.provisional.is_(False),
                )
                .order_by(ActivityVersion.version, ActivityVersion.id)
            )
        )
        items = rows[:5]
    if not 3 <= len(items) <= 5:
        raise ApiError(
            "validation_error",
            "A diagnostic needs between 3 and 5 questions",
            status_code=422,
        )
    return items


def suggested_skips(
    db: Session, answers: list[tuple[uuid.UUID, str]]
) -> list[str]:
    """Suggest competencies the learner may skip. Does not write evidence or skips."""
    suggestions: list[str] = []
    for activity_id, _choice in answers:
        activity = db.get(ActivityVersion, activity_id)
        if activity is None:
            continue
        lesson = db.get(Lesson, activity.lesson_id)
        if lesson is None:
            continue
        competency = db.get(Competency, lesson.competency_id)
        if competency is None:
            continue
        if competency.key not in suggestions:
            suggestions.append(competency.key)
    return suggestions[:5]


def skip_diagnostic(db: Session, user: User, goal: Goal) -> DiagnosticRun:
    if goal.domain_key == GENERAL_DOMAIN_KEY:
        raise ApiError(
            "validation_error",
            "Placement is not available for Something else",
            status_code=422,
        )
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
) -> tuple[DiagnosticRun, list[Attempt], list[str]]:
    if goal.domain_key == GENERAL_DOMAIN_KEY:
        raise ApiError(
            "validation_error",
            "Placement is not available for Something else",
            status_code=422,
        )
    if not answers or len(answers) > 5:
        raise ApiError(
            "validation_error",
            "Submit between 1 and 5 answers. You can submit the rest later.",
            status_code=422,
        )
    allowed = {item.id for item in start_diagnostic(db, user, goal)}
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
    return run, attempts, suggested_skips(db, answers)
