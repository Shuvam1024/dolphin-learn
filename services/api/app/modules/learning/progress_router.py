"""Owner-scoped evidence ledger grouped by goal. Not a mastery percentage."""

from __future__ import annotations

from datetime import datetime

from app.db import get_db
from app.modules.curriculum.models import Competency
from app.modules.goals.service import list_goals
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.learning.accept import activities_for, latest_accepted
from app.modules.learning.copy import facet_label
from app.modules.learning.models import (
    ActivityVersion,
    Attempt,
    CompetencyEvidence,
    CompetencyState,
    Evaluation,
    LearningPath,
    Lesson,
    PlanActivity,
    PlanVersion,
)
from app.modules.learning.reviews import queue_for_user
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(tags=["progress"])


class FacetOut(BaseModel):
    competency_key: str
    competency_name: str
    status_facet: str
    facet_label: str


class GoalCompetencyOut(BaseModel):
    name: str
    facet: str
    facet_label: str
    last_independent_at: str | None = None
    self_reported: bool = False


class GoalProgressOut(BaseModel):
    id: str
    title: str
    competencies: list[GoalCompetencyOut]
    unassessed_count: int


class UpcomingReviewOut(BaseModel):
    id: str
    competency_name: str
    lesson_title: str
    due_at: str
    due_now: bool
    reason: str


class ProgressOut(BaseModel):
    facets: list[FacetOut]
    unassessed: list[FacetOut]
    goals: list[GoalProgressOut] = []
    upcoming_reviews: list[UpcomingReviewOut] = []


def _unassessed(db: Session, user: User, known: set[str]) -> list[FacetOut]:
    rows = db.execute(
        select(Competency.key, Competency.name)
        .join(Lesson, Lesson.competency_id == Competency.id)
        .join(ActivityVersion, ActivityVersion.lesson_id == Lesson.id)
        .join(PlanActivity, PlanActivity.activity_version_id == ActivityVersion.id)
        .join(PlanVersion, PlanActivity.plan_version_id == PlanVersion.id)
        .join(LearningPath, PlanVersion.learning_path_id == LearningPath.id)
        .where(LearningPath.user_id == user.id, PlanVersion.status == "accepted")
    ).all()
    by_key = {key: name for key, name in rows if key not in known}
    return [
        FacetOut(
            competency_key=key,
            competency_name=by_key[key],
            status_facet="unassessed",
            facet_label=facet_label("unassessed"),
        )
        for key in sorted(by_key)
    ]


def _last_independent(db: Session, user: User) -> dict[str, datetime]:
    rows = db.execute(
        select(Competency.key, CompetencyEvidence.created_at)
        .join(Competency, Competency.id == CompetencyEvidence.competency_id)
        .where(
            CompetencyEvidence.user_id == user.id,
            CompetencyEvidence.status_facet == "independently_demonstrated",
        )
        .order_by(CompetencyEvidence.created_at.desc())
    ).all()
    latest: dict[str, datetime] = {}
    for key, created_at in rows:
        if key not in latest:
            latest[key] = created_at
    return latest


def _self_reported_keys(db: Session, user: User) -> set[str]:
    rows = db.execute(
        select(Competency.key)
        .join(Lesson, Lesson.competency_id == Competency.id)
        .join(ActivityVersion, ActivityVersion.lesson_id == Lesson.id)
        .join(Attempt, Attempt.activity_version_id == ActivityVersion.id)
        .join(Evaluation, Evaluation.attempt_id == Attempt.id)
        .where(
            Attempt.user_id == user.id,
            Evaluation.evaluator == "self_report",
            Evaluation.outcome == "self_reported",
        )
    ).all()
    return {key for (key,) in rows}


def _plan_competency_keys(db: Session, version: PlanVersion) -> list[tuple[str, str]]:
    seen: dict[str, str] = {}
    for row in activities_for(db, version):
        if row.activity_version_id is None:
            continue
        activity = db.get(ActivityVersion, row.activity_version_id)
        if activity is None:
            continue
        lesson = db.get(Lesson, activity.lesson_id)
        if lesson is None:
            continue
        competency = db.get(Competency, lesson.competency_id)
        if competency is None:
            continue
        seen.setdefault(competency.key, competency.name)
    return list(seen.items())


def build_progress(db: Session, user: User) -> dict[str, object]:
    state_rows = db.execute(
        select(Competency.key, Competency.name, CompetencyState.status_facet)
        .join(Competency, Competency.id == CompetencyState.competency_id)
        .where(CompetencyState.user_id == user.id)
        .order_by(Competency.key)
    ).all()
    facets = [
        FacetOut(
            competency_key=key,
            competency_name=name,
            status_facet=facet,
            facet_label=facet_label(facet),
        )
        for key, name, facet in state_rows
    ]
    facet_by_key = {item.competency_key: item for item in facets}
    independent = _last_independent(db, user)
    self_reported = _self_reported_keys(db, user)

    goal_rows: list[GoalProgressOut] = []
    for goal in list_goals(db, user):
        version = latest_accepted(db, user, goal)
        if version is None:
            continue
        competencies: list[GoalCompetencyOut] = []
        unassessed_count = 0
        for key, name in _plan_competency_keys(db, version):
            state = facet_by_key.get(key)
            if state is None:
                unassessed_count += 1
                competencies.append(
                    GoalCompetencyOut(
                        name=name,
                        facet="unassessed",
                        facet_label=facet_label("unassessed"),
                        last_independent_at=None,
                        self_reported=key in self_reported,
                    )
                )
            else:
                stamp = independent.get(key)
                competencies.append(
                    GoalCompetencyOut(
                        name=name,
                        facet=state.status_facet,
                        facet_label=state.facet_label,
                        last_independent_at=stamp.isoformat() if stamp else None,
                        self_reported=key in self_reported,
                    )
                )
        goal_rows.append(
            GoalProgressOut(
                id=str(goal.id),
                title=goal.title,
                competencies=competencies,
                unassessed_count=unassessed_count,
            )
        )

    reviews = queue_for_user(db, user)
    upcoming: list[UpcomingReviewOut] = []
    for item in list(reviews["due"]):
        upcoming.append(
            UpcomingReviewOut(
                id=str(item["id"]),
                competency_name=str(item.get("competency_name") or ""),
                lesson_title=str(item.get("lesson_title") or item.get("title") or ""),
                due_at=str(item["due_at"]),
                due_now=True,
                reason=str(item.get("reason") or ""),
            )
        )
    for item in list(reviews["scheduled"]):
        upcoming.append(
            UpcomingReviewOut(
                id=str(item["id"]),
                competency_name=str(item.get("competency_name") or ""),
                lesson_title=str(item.get("lesson_title") or item.get("title") or ""),
                due_at=str(item["due_at"]),
                due_now=False,
                reason=str(item.get("reason") or ""),
            )
        )

    return {
        "facets": facets,
        "unassessed": _unassessed(db, user, {item.competency_key for item in facets}),
        "goals": goal_rows,
        "upcoming_reviews": upcoming,
    }


@router.get("/progress", response_model=ProgressOut)
def get_progress(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ProgressOut:
    return ProgressOut.model_validate(build_progress(db, user))
