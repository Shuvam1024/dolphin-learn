"""Provisional AI outlines for General-route goals. Never graded."""

from __future__ import annotations

import re
from typing import Any

from app.errors import ApiError
from app.modules.ai_gateway.schemas import GatewayError
from app.modules.ai_gateway.service import complete, is_enabled
from app.modules.curriculum.models import Competency
from app.modules.goals.general import GENERAL_DOMAIN_KEY
from app.modules.goals.models import Goal
from app.modules.identity.models import User
from app.modules.learning.models import ActivityVersion, Lesson
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

_WORD = re.compile(r"\S+")
_ALLOWED_TYPES = frozenset({"reading", "free_recall", "reflection"})


class OutlineOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str = Field(min_length=1, max_length=200)
    reading_markdown: str = Field(min_length=1, max_length=4000)
    recall_prompt: str = Field(min_length=1, max_length=500)
    reflection_prompt: str = Field(min_length=1, max_length=500)

    @field_validator("reading_markdown")
    @classmethod
    def _words(cls, value: str) -> str:
        if len(_WORD.findall(value)) > 250:
            raise ValueError("reading_markdown must be 250 words or fewer")
        return value


class OutlinePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcomes: list[OutlineOutcome] = Field(min_length=1, max_length=5)


def build_outline_proposal(
    db: Session,
    user: User,
    goal: Goal,
) -> dict[str, Any]:
    if goal.domain_key != GENERAL_DOMAIN_KEY:
        raise ApiError(
            "validation_error",
            "Outlines are only for Something else goals",
            status_code=422,
        )
    competencies = list(
        db.scalars(
            select(Competency).where(
                Competency.goal_id == goal.id,
                Competency.owner_user_id == user.id,
            )
        )
    )
    if not competencies:
        raise ApiError(
            "validation_error",
            "Add outcomes before asking for an outline",
            status_code=422,
        )
    notes = ""
    first_lesson = db.scalar(
        select(Lesson).where(Lesson.competency_id == competencies[0].id)
    )
    if first_lesson is not None:
        notes = first_lesson.body_markdown
    variables = {
        "topic": goal.title,
        "outcomes": [item.name for item in competencies],
        "notes": notes[:2000],
    }
    if not is_enabled(db, user):
        return _deterministic(competencies, notes)

    try:
        raw = complete(db, user, "general_outline", variables, OutlinePayload)
    except GatewayError:
        return _deterministic(competencies, notes)
    assert isinstance(raw, OutlinePayload)
    return {
        "outcomes": [item.model_dump() for item in raw.outcomes],
        "source": "ai",
        "provisional": True,
        "note": "Draft by the tutor — edit or remove",
    }


def accept_outline(
    db: Session,
    user: User,
    goal: Goal,
    outcomes: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Replace gather-material prompts with provisional AI drafts. Never graded types."""
    if goal.domain_key != GENERAL_DOMAIN_KEY:
        raise ApiError(
            "validation_error",
            "Outlines are only for Something else goals",
            status_code=422,
        )
    competencies = list(
        db.scalars(
            select(Competency)
            .where(Competency.goal_id == goal.id, Competency.owner_user_id == user.id)
            .order_by(Competency.key)
        )
    )
    applied: list[dict[str, str]] = []
    for index, competency in enumerate(competencies):
        if index >= len(outcomes):
            break
        payload = outcomes[index]
        reading = str(payload.get("reading_markdown") or "").strip()
        recall = str(payload.get("recall_prompt") or "").strip()
        reflection = str(payload.get("reflection_prompt") or "").strip()
        if not reading or not recall:
            continue
        lesson = db.scalar(select(Lesson).where(Lesson.competency_id == competency.id))
        if lesson is None:
            continue
        lesson.body_markdown = reading
        lesson.source = "ai"
        lesson.provisional = True
        activities = list(
            db.scalars(
                select(ActivityVersion).where(ActivityVersion.lesson_id == lesson.id)
            )
        )
        for activity in activities:
            if activity.activity_type not in _ALLOWED_TYPES:
                raise ApiError(
                    "validation_error",
                    "Outline items must be reading, free recall, or reflection",
                    status_code=422,
                )
            if activity.answer_key is not None:
                raise ApiError(
                    "validation_error",
                    "Outline items cannot include an answer key",
                    status_code=422,
                )
            activity.provisional = True
            activity.source = "ai"
            if activity.activity_type == "reading":
                activity.payload = {"body_markdown": reading}
                activity.prompt = "Read your draft notes"
            elif activity.activity_type == "free_recall":
                activity.prompt = recall
            elif activity.activity_type == "reflection":
                activity.prompt = reflection or activity.prompt
        applied.append({"competency_key": competency.key, "status": "updated"})
    db.commit()
    return applied


def delete_provisional_item(
    db: Session, user: User, goal: Goal, activity_id: str
) -> None:
    from uuid import UUID

    activity = db.get(ActivityVersion, UUID(activity_id))
    if activity is None:
        raise ApiError("not_found", "Item not found", status_code=404)
    lesson = db.get(Lesson, activity.lesson_id)
    if lesson is None:
        raise ApiError("not_found", "Item not found", status_code=404)
    competency = db.get(Competency, lesson.competency_id)
    if (
        competency is None
        or competency.owner_user_id != user.id
        or competency.goal_id != goal.id
    ):
        raise ApiError("not_found", "Item not found", status_code=404)
    if not activity.provisional:
        raise ApiError(
            "validation_error",
            "Only draft items can be removed this way",
            status_code=422,
        )
    db.delete(activity)
    db.commit()


def _deterministic(competencies: list[Competency], notes: str) -> dict[str, Any]:
    outcomes = []
    for competency in competencies:
        outcomes.append(
            {
                "statement": competency.name,
                "reading_markdown": notes
                or f"Gather a short reading about: {competency.name}",
                "recall_prompt": f"From memory, write what you can about: {competency.name}",
                "reflection_prompt": f"How will you use: {competency.name}",
            }
        )
    return {
        "outcomes": outcomes,
        "source": "fallback",
        "provisional": True,
        "note": "Draft by the tutor — edit or remove",
    }
