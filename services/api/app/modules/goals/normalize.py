"""Suggest a title, subject, and outcomes from free text. Nothing is saved."""

from __future__ import annotations

from typing import Any

from app.errors import ApiError
from app.modules.ai_gateway.schemas import GatewayError
from app.modules.ai_gateway.service import complete, is_enabled
from app.modules.curriculum.models import Domain
from app.modules.goals.general import GENERAL_DOMAIN_KEY
from app.modules.identity.models import User
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session


class GoalNormalizeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(max_length=60)
    domain_key: str
    outcomes: list[str] = Field(min_length=1, max_length=5)
    minutes_hint_per_outcome: int = Field(ge=1, le=120)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be empty")
        return cleaned[:60]

    @field_validator("outcomes")
    @classmethod
    def _outcomes(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            text = item.strip()
            if not text:
                continue
            if not text.lower().startswith("i can"):
                text = f"I can {text[0].lower() + text[1:]}" if text else text
            cleaned.append(text[:200])
        if not cleaned:
            raise ValueError("at least one outcome is required")
        return cleaned[:5]


def allowed_domains(db: Session) -> set[str]:
    keys = {row.key for row in db.scalars(select(Domain))}
    keys.add(GENERAL_DOMAIN_KEY)
    return keys


def validate_normalize(payload: GoalNormalizeOut, allowed: set[str]) -> GoalNormalizeOut:
    if payload.domain_key not in allowed:
        raise ApiError(
            "validation_error",
            "That subject is not available yet",
            status_code=422,
        )
    return payload


def normalize_goal(
    db: Session,
    user: User,
    text: str,
) -> dict[str, Any]:
    cleaned = text.strip()
    if not cleaned:
        raise ApiError(
            "validation_error",
            "Write what you want to learn",
            status_code=422,
        )
    if not is_enabled(db, user):
        raise ApiError(
            "not_found",
            "Suggestions are not available right now",
            status_code=404,
        )
    allowed = allowed_domains(db)
    try:
        raw = complete(
            db,
            user,
            "goal_normalize",
            {
                "text": cleaned[:2000],
                "allowed_domain_keys": sorted(allowed),
            },
            GoalNormalizeOut,
        )
    except GatewayError as exc:
        raise ApiError(
            "not_found",
            "Suggestions are not available right now",
            status_code=404,
        ) from exc
    assert isinstance(raw, GoalNormalizeOut)
    validated = validate_normalize(raw, allowed)
    return {
        "title": validated.title,
        "domain_key": validated.domain_key,
        "outcomes": validated.outcomes,
        "minutes_hint_per_outcome": validated.minutes_hint_per_outcome,
        "confidence": validated.confidence,
        "source": "ai",
    }
