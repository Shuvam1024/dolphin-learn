"""General route: learner-owned competencies and lessons for any subject."""

from __future__ import annotations

import html
import re
import uuid

from app.errors import ApiError
from app.modules.curriculum.models import Competency, Domain
from app.modules.goals.models import Goal
from app.modules.identity.models import User
from app.modules.learning.models import ActivityVersion, Lesson
from sqlalchemy import select
from sqlalchemy.orm import Session

GENERAL_DOMAIN_KEY = "general"
GENERAL_DOMAIN_NAME = "Something else"
_NOTES_LIMIT = 20_000
_TAG = re.compile(r"<[^>]+>")
_SLUG = re.compile(r"[^a-z0-9]+")


def ensure_general_domain(db: Session) -> Domain:
    found = db.scalar(select(Domain).where(Domain.key == GENERAL_DOMAIN_KEY))
    if found is not None:
        return found
    row = Domain(key=GENERAL_DOMAIN_KEY, name=GENERAL_DOMAIN_NAME)
    db.add(row)
    db.flush()
    return row


def sanitize_notes(value: str | None) -> str:
    if value is None:
        return ""
    cleaned = _TAG.sub("", value)
    cleaned = html.unescape(cleaned).strip()
    if len(cleaned) > _NOTES_LIMIT:
        raise ApiError(
            "payload_too_large",
            f"Notes must be {_NOTES_LIMIT} characters or fewer",
            status_code=413,
        )
    return cleaned


def slugify(text: str) -> str:
    folded = text.casefold().strip()
    slug = _SLUG.sub("-", folded).strip("-")
    return (slug[:40] or "outcome")


def _minutes(outcome: dict[str, object]) -> int:
    raw = outcome.get("minutes")
    if raw is None:
        return 10
    try:
        value = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ApiError(
            "validation_error",
            "Outcome minutes must be a whole number",
            status_code=422,
        ) from exc
    if value < 1:
        raise ApiError(
            "validation_error",
            "Outcome minutes must be at least 1",
            status_code=422,
        )
    return value


def validate_general_payload(payload: dict[str, object] | None) -> dict[str, object]:
    if payload is None:
        raise ApiError(
            "validation_error",
            "Add a topic and one to five outcomes for Something else",
            status_code=422,
        )
    topic = str(payload.get("topic") or "").strip()
    if not topic:
        raise ApiError(
            "validation_error",
            "Add a topic for Something else",
            status_code=422,
        )
    outcomes_raw = payload.get("outcomes")
    if not isinstance(outcomes_raw, list) or not (1 <= len(outcomes_raw) <= 5):
        raise ApiError(
            "validation_error",
            "Add one to five outcomes you want to be able to do",
            status_code=422,
        )
    outcomes: list[dict[str, object]] = []
    for item in outcomes_raw:
        if not isinstance(item, dict):
            raise ApiError(
                "validation_error",
                "Each outcome needs a statement",
                status_code=422,
            )
        statement = str(item.get("statement") or "").strip()
        if not statement:
            raise ApiError(
                "validation_error",
                "Each outcome needs a statement",
                status_code=422,
            )
        outcomes.append({"statement": statement, "minutes": _minutes(item)})
    notes = sanitize_notes(
        None if payload.get("notes_markdown") is None else str(payload.get("notes_markdown"))
    )
    return {"topic": topic, "outcomes": outcomes, "notes_markdown": notes}


def create_owned_curriculum(
    db: Session,
    user: User,
    goal: Goal,
    *,
    topic: str,
    outcomes: list[dict[str, object]],
    notes_markdown: str,
) -> list[Competency]:
    domain = ensure_general_domain(db)
    goal_slug = str(goal.id).replace("-", "")[:8]
    created: list[Competency] = []
    gather = (
        notes_markdown.strip()
        or (
            f"Gather a short reading or notes about: {topic}. "
            "Paste or write what you want to remember, then try recalling it."
        )
    )
    for index, outcome in enumerate(outcomes, start=1):
        statement = str(outcome["statement"])
        minutes = int(outcome["minutes"])
        low = minutes
        high = max(minutes, int(round(minutes * 1.5)))
        slug = slugify(statement)
        key = f"general.{goal_slug}.{slug}"
        # Avoid collisions within the same goal
        existing = db.scalar(select(Competency).where(Competency.key == key))
        if existing is not None:
            key = f"{key}-{index}"
        competency = Competency(
            domain_id=domain.id,
            key=key,
            name=statement[:200],
            owner_user_id=user.id,
            goal_id=goal.id,
        )
        db.add(competency)
        db.flush()
        lesson = Lesson(
            competency_id=competency.id,
            key=f"{key}.intro",
            title=statement[:200],
            body_markdown=gather,
            provisional=False,
            source="learner",
            owner_user_id=user.id,
        )
        db.add(lesson)
        db.flush()
        share = max(1, low // 3)
        share_high = max(share, high // 3)
        activities = [
            (
                "reading",
                "Read your notes",
                gather,
                share,
                share_high,
            ),
            (
                "free_recall",
                "Write what you remember",
                f"From memory, write what you can about: {statement}",
                share,
                share_high,
            ),
            (
                "reflection",
                "How will you use this?",
                f"In one or two sentences, how will you use: {statement}",
                max(1, low - 2 * share),
                max(1, high - 2 * share_high),
            ),
        ]
        for position, (activity_type, title, prompt, effort_low, effort_high) in enumerate(
            activities, start=1
        ):
            db.add(
                ActivityVersion(
                    lesson_id=lesson.id,
                    version=position,
                    item_id=f"{key}-{activity_type}",
                    activity_type=activity_type,
                    prompt=prompt if activity_type != "reading" else title,
                    answer_key=None,
                    explanation=None,
                    misconceptions=None,
                    payload=(
                        {"body_markdown": gather}
                        if activity_type == "reading"
                        else {"reveal_lesson": True}
                        if activity_type == "free_recall"
                        else {}
                    ),
                    provisional=False,
                    source="learner",
                    effort_minutes_low=effort_low,
                    effort_minutes_high=effort_high,
                )
            )
        created.append(competency)
    db.flush()
    return created


def owned_competency_visible(db: Session, user: User, competency: Competency) -> bool:
    if competency.owner_user_id is None:
        return True
    return competency.owner_user_id == user.id


def get_owned_competency(
    db: Session, user: User, competency_id: uuid.UUID
) -> Competency:
    competency = db.get(Competency, competency_id)
    if competency is None or not owned_competency_visible(db, user, competency):
        raise ApiError("not_found", "Not found", status_code=404)
    return competency
