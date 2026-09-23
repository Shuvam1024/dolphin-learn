"""Due queue and review attempts."""

import uuid
from typing import Literal

from app.db import get_db
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.learning.reviews import queue_for_user, reveal_solution, submit_review_attempt
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

router = APIRouter(prefix="/reviews", tags=["reviews"])


class ReviewOut(BaseModel):
    id: str
    competency_key: str
    due_at: str
    interval_days: int
    reason: str
    title: str
    prompt: str
    revealed_choice: str = ""


class QueueOut(BaseModel):
    due: list[ReviewOut]
    scheduled: list[ReviewOut]


class SolutionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["guided", "challenge"] = "guided"


class AttemptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    choice: Literal["a", "b", "c"]

    @field_validator("choice", mode="before")
    @classmethod
    def _choice(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class AttemptOut(BaseModel):
    id: str
    outcome: str
    assistance: str
    interval_days: int
    due_at: str
    extended: bool


@router.get("/due", response_model=QueueOut)
def get_due(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> QueueOut:
    return QueueOut.model_validate(queue_for_user(db, user))


@router.post("/{review_id}/solution")
def post_solution(
    review_id: uuid.UUID,
    body: SolutionIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return reveal_solution(db, user, review_id, mode=body.mode)


@router.post("/{review_id}/attempts", response_model=AttemptOut)
def post_attempt(
    review_id: uuid.UUID,
    body: AttemptIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> AttemptOut:
    return AttemptOut.model_validate(
        submit_review_attempt(db, user, review_id, choice=body.choice)
    )
