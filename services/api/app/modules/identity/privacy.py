"""Export and account deletion for privacy (S98/S99)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.analytics.events import ProductEvent, emit_account_deletion_requested, emit_account_export_requested
from app.config import settings
from app.db import get_db
from app.errors import ApiError
from app.modules.ai_gateway.models import AiCall
from app.modules.curriculum.models import Competency
from app.modules.goals.models import Goal
from app.modules.identity.deps import current_user
from app.modules.identity.models import LearnerProfile, User
from app.modules.identity.tokens import revoke_access_token
from app.modules.learner_model.effort import LearnerEffortFactor
from app.modules.learning.models import (
    Attempt,
    CompetencyEvidence,
    CompetencyState,
    Lesson,
    ReviewItem,
)
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter()


def _rate_limited(db: Session, user_id: uuid.UUID, name: str, *, limit: int, hours: int) -> bool:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    count = db.scalar(
        select(func.count())
        .select_from(ProductEvent)
        .where(
            ProductEvent.user_id == user_id,
            ProductEvent.name == name,
            ProductEvent.created_at >= since,
        )
    )
    return int(count or 0) >= limit


@router.get("/me/export")
def export_my_data(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Download everything Dolphin holds about you (no raw AI prompts)."""
    if _rate_limited(db, user.id, "account_export_requested", limit=3, hours=1):
        raise ApiError("rate_limited", "Export limit is 3 per hour", status_code=429)

    profile = db.get(LearnerProfile, user.id)
    goals = list(db.scalars(select(Goal).where(Goal.user_id == user.id)))
    owned = list(
        db.execute(
            select(Competency.key, Competency.name, Lesson.key, Lesson.title)
            .outerjoin(Lesson, Lesson.competency_id == Competency.id)
            .where(Competency.owner_user_id == user.id)
        ).all()
    )
    ai_meta = list(
        db.scalars(
            select(AiCall)
            .where(AiCall.user_id == user.id)
            .order_by(AiCall.created_at.desc())
            .limit(500)
        )
    )
    factors = list(db.scalars(select(LearnerEffortFactor).where(LearnerEffortFactor.user_id == user.id)))
    attempts = list(db.scalars(select(Attempt).where(Attempt.user_id == user.id).limit(2000)))
    evidence = list(db.scalars(select(CompetencyEvidence).where(CompetencyEvidence.user_id == user.id)))
    states = list(db.scalars(select(CompetencyState).where(CompetencyState.user_id == user.id)))
    reviews = list(db.scalars(select(ReviewItem).where(ReviewItem.user_id == user.id)))

    emit_account_export_requested(db, user.id)
    db.commit()

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {"id": str(user.id), "email": user.email, "auth_subject": user.auth_subject},
        "profile": None
        if profile is None
        else {
            "display_name": profile.display_name,
            "timezone": profile.timezone,
            "locale": profile.locale,
            "a11y_prefs": profile.a11y_prefs,
            "default_session_minutes": profile.default_session_minutes,
            "ai_opt_out": profile.ai_opt_out,
            "adult_acknowledged_at": profile.adult_acknowledged_at.isoformat()
            if profile.adult_acknowledged_at
            else None,
        },
        "goals": [
            {
                "id": str(g.id),
                "title": g.title,
                "domain_key": g.domain_key,
                "status": g.status,
                "priority": g.priority,
            }
            for g in goals
        ],
        "owned_competencies_lessons": [
            {
                "competency_key": row[0],
                "competency_name": row[1],
                "lesson_key": row[2],
                "lesson_title": row[3],
            }
            for row in owned
        ],
        "ai_calls": [
            {
                "prompt_id": row.prompt_id,
                "prompt_version": row.prompt_version,
                "model": row.model,
                "tokens_in": row.tokens_in,
                "tokens_out": row.tokens_out,
                "latency_ms": row.latency_ms,
                "outcome": row.outcome,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in ai_meta
        ],
        "effort_factors": [
            {
                "activity_type": row.activity_type,
                "factor": row.factor,
                "observations": row.observations,
            }
            for row in factors
        ],
        "attempts": [
            {
                "id": str(row.id),
                "activity_version_id": str(row.activity_version_id),
                "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
                "response_keys": sorted((row.response or {}).keys()),
            }
            for row in attempts
        ],
        "evidence": [
            {
                "competency_id": str(row.competency_id),
                "status_facet": row.status_facet,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in evidence
        ],
        "competency_state": [
            {"competency_id": str(row.competency_id), "status_facet": row.status_facet} for row in states
        ],
        "reviews": [
            {
                "id": str(row.id),
                "competency_id": str(row.competency_id),
                "due_at": row.due_at.isoformat() if row.due_at else None,
                "interval_days": row.interval_days,
            }
            for row in reviews
        ],
    }


class DeleteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: str = Field(min_length=1)


@router.delete("/me")
def delete_my_account(
    body: DeleteIn,
    authorization: str | None = Header(default=None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Tombstone the account. Purge job removes data after RETENTION_DAYS."""
    if body.confirm != "DELETE":
        raise ApiError(
            "validation_error",
            'Send confirm: "DELETE" to delete your account',
            status_code=422,
        )
    emit_account_deletion_requested(db, user.id)
    user.email = f"deleted+{user.id}@invalid.local"
    user.auth_subject = f"deleted|{user.id}"
    user.deleted_at = datetime.now(timezone.utc)
    profile = db.get(LearnerProfile, user.id)
    if profile is not None:
        profile.display_name = None
        profile.ai_opt_out = True
    db.commit()

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            revoke_access_token(db, token, user_id=user.id)
        except ApiError:
            pass

    return {
        "deleted": True,
        "retention_days": int(settings.retention_days),
        "message": f"Account scheduled for purge after {settings.retention_days} days.",
    }
