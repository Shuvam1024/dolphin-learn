"""Owner-scoped competency facets. This is not a mastery percentage."""

from app.db import get_db
from app.modules.curriculum.models import Competency
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.learning.copy import facet_label
from app.modules.learning.models import (
    ActivityVersion,
    CompetencyState,
    LearningPath,
    Lesson,
    PlanActivity,
    PlanVersion,
)
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


class ProgressOut(BaseModel):
    facets: list[FacetOut]
    unassessed: list[FacetOut]


def _names(db: Session, keys: set[str]) -> dict[str, str]:
    if not keys:
        return {}
    rows = db.execute(select(Competency.key, Competency.name).where(Competency.key.in_(keys)))
    return {key: name for key, name in rows}


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


@router.get("/progress", response_model=ProgressOut)
def get_progress(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ProgressOut:
    rows = db.execute(
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
        for key, name, facet in rows
    ]
    return ProgressOut(
        facets=facets,
        unassessed=_unassessed(db, user, {item.competency_key for item in facets}),
    )
