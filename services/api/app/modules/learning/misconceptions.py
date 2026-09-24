"""AI misconception notes for typed wrong answers. Advisory only — never changes grade."""

from __future__ import annotations

import re

from app.modules.ai_gateway.schemas import GatewayError
from app.modules.ai_gateway.service import complete, is_enabled
from app.modules.identity.models import User
from app.modules.learning.models import ActivityVersion
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

_ANSWER_PHRASE = re.compile(r"\bthe answer is\b", re.I)


class MisconceptionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str = Field(max_length=240)
    tag: str = Field(max_length=64)


def _allowed_tags(activity: ActivityVersion) -> set[str]:
    tags = {"other"}
    notes = activity.misconceptions
    if isinstance(notes, dict):
        tags.update(str(key) for key in notes)
    return tags


def note_rejects_answer(activity: ActivityVersion, note: str) -> bool:
    text = note.strip()
    if not text or _ANSWER_PHRASE.search(text):
        return True
    folded = text.casefold()
    expected = ""
    if activity.answer_key is not None:
        expected = str(activity.answer_key.get("correct", "")).strip()
    if expected and expected.casefold() in folded:
        return True
    payload = activity.payload or {}
    alternates = payload.get("alternates") if isinstance(payload, dict) else None
    if isinstance(alternates, list):
        for alt in alternates:
            if str(alt).strip() and str(alt).casefold() in folded:
                return True
    return False


def maybe_ai_misconception(
    db: Session,
    user: User,
    activity: ActivityVersion,
    *,
    learner_response: str,
) -> dict[str, object] | None:
    if not is_enabled(db, user):
        return None
    expected = ""
    if activity.answer_key is not None:
        expected = str(activity.answer_key.get("correct", ""))
    try:
        result = complete(
            db,
            user,
            "misconception_note",
            {
                "prompt": activity.prompt,
                "expected": expected,
                "learner_response": learner_response,
                "explanation": activity.explanation or "",
                "allowed_tags": sorted(_allowed_tags(activity)),
            },
            MisconceptionOut,
            timeout=12.0,
        )
        assert isinstance(result, MisconceptionOut)
    except GatewayError:
        return None
    if note_rejects_answer(activity, result.note):
        return None
    tag = result.tag if result.tag in _allowed_tags(activity) else "other"
    return {
        "misconception_note": result.note.strip(),
        "misconception_source": "ai",
        "tag": tag,
    }
