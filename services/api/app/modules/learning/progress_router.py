"""Owner-scoped competency facets. This is not a mastery percentage."""

from app.db import get_db
from app.modules.curriculum.models import Competency
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.learning.models import CompetencyState
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(tags=["progress"])


class FacetOut(BaseModel):
    competency_key: str
    status_facet: str


class ProgressOut(BaseModel):
    facets: list[FacetOut]


@router.get("/progress", response_model=ProgressOut)
def get_progress(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ProgressOut:
    rows = db.execute(
        select(Competency.key, CompetencyState.status_facet)
        .join(Competency, Competency.id == CompetencyState.competency_id)
        .where(CompetencyState.user_id == user.id)
        .order_by(Competency.key)
    ).all()
    return ProgressOut(
        facets=[FacetOut(competency_key=key, status_facet=facet) for key, facet in rows]
    )
