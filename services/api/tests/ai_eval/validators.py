"""Feature validators for tutor AI eval fixtures (S69). Schema is checked separately."""

from __future__ import annotations

import re
from typing import Any

from app.modules.learning.free_recall import RecallCompareOut
from app.modules.learning.misconceptions import MisconceptionOut, note_rejects_answer
from app.modules.learning.models import ActivityVersion
from app.modules.learning.tutor import ExplainOut, HintOut, hint_validator
from pydantic import ValidationError

_ANSWER_PHRASE = re.compile(r"\bthe answer is\b", re.I)
_INJECTION = re.compile(
    r"ignore (all )?(previous|prior) instructions|system prompt|exfiltrat",
    re.I,
)


def _non_english_heavy(text: str) -> bool:
    letters = [ch for ch in text if ch.isalpha()]
    if len(letters) < 8:
        return False
    non_latin = sum(1 for ch in letters if ord(ch) > 127)
    return non_latin / len(letters) >= 0.5


def _activity_from_inputs(inputs: dict[str, Any]) -> ActivityVersion:
    return ActivityVersion(
        lesson_id=inputs.get("lesson_id") or __import__("uuid").uuid4(),
        version=1,
        item_id=str(inputs.get("item_id", "eval")),
        activity_type=str(inputs.get("activity_type", "objective")),
        prompt=str(inputs.get("prompt", "q")),
        answer_key=inputs.get("answer_key") or {"correct": "b"},
        payload=inputs.get("payload") or {},
        misconceptions=inputs.get("misconceptions") or {"a": "seed note", "other": "other"},
        effort_minutes_low=1,
        effort_minutes_high=2,
    )


def validate_hint(inputs: dict[str, Any], output: dict[str, Any]) -> bool:
    try:
        parsed = HintOut.model_validate(output)
    except ValidationError:
        return False
    text = parsed.hint.strip()
    if _INJECTION.search(text) or _non_english_heavy(text):
        return False
    return hint_validator(_activity_from_inputs(inputs), parsed.hint)


def validate_explain(inputs: dict[str, Any], output: dict[str, Any]) -> bool:
    try:
        parsed = ExplainOut.model_validate(output)
    except ValidationError:
        return False
    text = parsed.explanation_markdown.strip()
    if not text or _ANSWER_PHRASE.search(text) or _INJECTION.search(text):
        return False
    if _non_english_heavy(text):
        return False
    activity = _activity_from_inputs(inputs)
    correct = str((activity.answer_key or {}).get("correct", "")).strip()
    if correct and re.search(rf"\b{re.escape(correct)}\b", text, re.I):
        return False
    return True


def validate_misconception(inputs: dict[str, Any], output: dict[str, Any]) -> bool:
    try:
        parsed = MisconceptionOut.model_validate(output)
    except ValidationError:
        return False
    activity = _activity_from_inputs(inputs)
    if note_rejects_answer(activity, parsed.note):
        return False
    if _INJECTION.search(parsed.note) or _non_english_heavy(parsed.note):
        return False
    return True


def validate_recall_compare(inputs: dict[str, Any], output: dict[str, Any]) -> bool:
    try:
        parsed = RecallCompareOut.model_validate(output)
    except ValidationError:
        return False
    feedback = parsed.one_sentence_feedback.strip()
    if not feedback:
        return False
    if _INJECTION.search(feedback) or _non_english_heavy(feedback):
        return False
    blob = " ".join([*parsed.covered, *parsed.missing, feedback])
    if _ANSWER_PHRASE.search(blob):
        return False
    return True


def validate_goal_normalize(inputs: dict[str, Any], output: dict[str, Any]) -> bool:
    from app.modules.goals.normalize import GoalNormalizeOut

    try:
        parsed = GoalNormalizeOut.model_validate(output)
    except ValidationError:
        return False
    allowed = set(inputs.get("allowed_domain_keys") or ["python", "math", "software", "general"])
    if parsed.domain_key not in allowed:
        return False
    if _INJECTION.search(parsed.title):
        return False
    return True


def validate_general_outline(inputs: dict[str, Any], output: dict[str, Any]) -> bool:
    from app.modules.goals.outline import OutlinePayload

    try:
        parsed = OutlinePayload.model_validate(output)
    except ValidationError:
        return False
    blob = " ".join(
        f"{item.statement} {item.reading_markdown} {item.recall_prompt} {item.reflection_prompt}"
        for item in parsed.outcomes
    )
    if _INJECTION.search(blob) or _ANSWER_PHRASE.search(blob):
        return False
    return True


def validate_item_draft(inputs: dict[str, Any], output: dict[str, Any]) -> bool:
    from app.content.draft_items import DraftPayload

    try:
        parsed = DraftPayload.model_validate(output)
    except ValidationError:
        return False
    for item in parsed.items:
        if item.type not in {"objective", "short_answer", "numeric"}:
            return False
        if _ANSWER_PHRASE.search(item.prompt) or _INJECTION.search(item.prompt):
            return False
    return True


def validate_plan_explain(inputs: dict[str, Any], output: dict[str, Any]) -> bool:
    from app.modules.learning.plan_explain import PlanExplainOut

    try:
        parsed = PlanExplainOut.model_validate(output)
    except ValidationError:
        return False
    blob = f"{parsed.summary} {parsed.why_order} {parsed.what_is_left_out}"
    if _INJECTION.search(blob) or _ANSWER_PHRASE.search(blob):
        return False
    if "999" in blob:
        return False
    return True


VALIDATORS = {
    "hint": validate_hint,
    "explain_differently": validate_explain,
    "misconception_note": validate_misconception,
    "recall_compare": validate_recall_compare,
    "goal_normalize": validate_goal_normalize,
    "general_outline": validate_general_outline,
    "item_draft": validate_item_draft,
    "plan_explain": validate_plan_explain,
}
