"""Signed-in Home projection. No streak counters."""

from app.db import get_db
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.learning.home import build_home
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(tags=["home"])


class NextActionOut(BaseModel):
    kind: str
    title: str
    subtitle: str = ""
    minutes_estimate: int = 0
    href: str
    goal_id: str


class GoalCardOut(BaseModel):
    id: str
    title: str
    subject_name: str = ""
    next_lesson_title: str = ""
    remaining_minutes: int = 0
    usable_minutes: int = 0
    studied_minutes: int = 0
    status: str = "active"
    feasibility_note: str = ""


class DueReviewItemOut(BaseModel):
    competency_key: str
    competency_name: str
    reason: str


class DueReviewsOut(BaseModel):
    count: int
    minutes_estimate: int = 0
    first_lesson_title: str = ""
    items: list[DueReviewItemOut] = Field(default_factory=list)


class EvidenceOut(BaseModel):
    competency_key: str
    competency_name: str
    facet: str = ""
    status_facet: str = ""
    facet_label: str


class QuickLearnOut(BaseModel):
    href: str
    label: str


class HomeOut(BaseModel):
    next_action: NextActionOut
    goals: list[GoalCardOut]
    due_reviews: DueReviewsOut
    recent_evidence: list[EvidenceOut]
    quick_learn: QuickLearnOut


@router.get("/home", response_model=HomeOut)
def get_home(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> HomeOut:
    return HomeOut.model_validate(build_home(db, user))
