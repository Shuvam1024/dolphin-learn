"""Signed-in Home projection. No streak counters."""

from app.db import get_db
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.learning.home import build_home
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(tags=["home"])


class NextActionOut(BaseModel):
    kind: str
    title: str
    href: str
    goal_id: str


class GoalCardOut(BaseModel):
    id: str
    title: str
    feasibility_note: str
    usable_minutes: int = 0
    studied_minutes: int = 0


class DueReviewOut(BaseModel):
    competency_key: str
    reason: str


class EvidenceOut(BaseModel):
    competency_key: str
    status_facet: str


class QuickLearnOut(BaseModel):
    href: str
    label: str


class HomeOut(BaseModel):
    next_action: NextActionOut
    goals: list[GoalCardOut]
    due_reviews: list[DueReviewOut]
    recent_evidence: list[EvidenceOut]
    quick_learn: QuickLearnOut


@router.get("/home", response_model=HomeOut)
def get_home(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> HomeOut:
    return HomeOut.model_validate(build_home(db, user))
