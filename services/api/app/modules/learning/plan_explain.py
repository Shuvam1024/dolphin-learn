"""Explain a plan proposal in the learner's words. AI is advisory; planner stays deterministic."""

from __future__ import annotations

import re
from typing import Any

from app.modules.ai_gateway.schemas import GatewayError
from app.modules.ai_gateway.service import complete, is_enabled
from app.modules.identity.models import User
from app.modules.learning.copy import reason_text
from app.modules.learning.planner import PlanProposal
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

_TITLE_PHRASE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")
_NUMBER = re.compile(r"\d+")

# Cache explanations by proposal hash for the process lifetime.
_CACHE: dict[str, dict[str, str]] = {}


class PlanExplainOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(max_length=500)
    why_order: str = Field(max_length=300)
    what_is_left_out: str = Field(max_length=300)


def allowed_numbers_for(proposal: PlanProposal, *, remaining: int | None = None) -> set[int]:
    numbers: set[int] = {
        proposal.usable_minutes,
        proposal.estimated_required_low,
        proposal.estimated_required_high,
        proposal.review_reserve_minutes,
        proposal.learning_minutes,
        len(proposal.included),
        len(proposal.deferred),
    }
    if remaining is not None:
        numbers.add(remaining)
    for item in proposal.included:
        numbers.add(item.effort_low)
        numbers.add(item.effort_high)
        if item.position is not None:
            numbers.add(item.position)
    for item in proposal.deferred:
        numbers.add(item.effort_low)
        numbers.add(item.effort_high)
    return {n for n in numbers if n is not None}


def allowed_names_for(proposal: PlanProposal) -> set[str]:
    names = {item.name for item in proposal.included}
    names |= {item.name for item in proposal.deferred}
    return {name for name in names if name}


def validate_plan_explain(
    payload: PlanExplainOut | dict[str, str],
    *,
    allowed_names: set[str],
    allowed_numbers: set[int],
) -> bool:
    if isinstance(payload, PlanExplainOut):
        fields = [payload.summary, payload.why_order, payload.what_is_left_out]
    else:
        fields = [
            str(payload.get("summary", "")),
            str(payload.get("why_order", "")),
            str(payload.get("what_is_left_out", "")),
        ]
    if any(not field.strip() for field in fields):
        return False
    if any(len(field) > limit for field, limit in zip(fields, (500, 300, 300), strict=True)):
        return False
    combined = " ".join(fields)
    for match in _NUMBER.finditer(combined):
        if int(match.group()) not in allowed_numbers:
            return False
    allowed_folded = {name.casefold() for name in allowed_names}
    for match in _TITLE_PHRASE.finditer(combined):
        phrase = match.group(1)
        if phrase.casefold() not in allowed_folded:
            return False
    return True


def deterministic_explanation(proposal: PlanProposal, *, remaining: int | None = None) -> dict[str, str]:
    included = ", ".join(item.name for item in proposal.included) or "nothing yet"
    deferred = ", ".join(
        f"{item.name} ({reason_text(item.reason_code)})" for item in proposal.deferred
    )
    left = remaining if remaining is not None else proposal.usable_minutes
    summary = (
        f"This plan uses about {left} minutes with a focus on {proposal.priority_label}. "
        f"It includes {included}."
    )[:500]
    why_order = (
        f"{proposal.priority_effect} Lessons follow prerequisites, then the next unfinished topic."
    )[:300]
    what_is_left_out = (
        f"Not in this plan: {deferred}." if deferred else "Nothing was deferred this time."
    )[:300]
    return {
        "summary": summary,
        "why_order": why_order,
        "what_is_left_out": what_is_left_out,
        "source": "deterministic",
    }


def explain_plan(
    db: Session,
    user: User,
    proposal: PlanProposal,
    *,
    proposal_hash: str,
    goal_text: str,
    remaining_minutes: int | None = None,
) -> dict[str, str]:
    cache_key = proposal_hash.strip()
    if cache_key in _CACHE:
        cached = dict(_CACHE[cache_key])
        return cached

    fallback = deterministic_explanation(proposal, remaining=remaining_minutes)
    if not is_enabled(db, user):
        _CACHE[cache_key] = dict(fallback)
        return fallback

    names = allowed_names_for(proposal)
    numbers = allowed_numbers_for(proposal, remaining=remaining_minutes)
    variables: dict[str, Any] = {
        "goal_text": goal_text,
        "priority": proposal.priority_label,
        "priority_effect": proposal.priority_effect,
        "usable_minutes": proposal.usable_minutes,
        "remaining_minutes": remaining_minutes
        if remaining_minutes is not None
        else proposal.usable_minutes,
        "included": [
            {
                "name": item.name,
                "effort_low": item.effort_low,
                "effort_high": item.effort_high,
            }
            for item in proposal.included
        ],
        "deferred": [
            {
                "name": item.name,
                "reason_code": item.reason_code,
                "reason_text": reason_text(item.reason_code),
            }
            for item in proposal.deferred
        ],
        "allowed_numbers": sorted(numbers),
    }
    try:
        result = complete(db, user, "plan_explain", variables, PlanExplainOut, timeout=12.0)
        assert isinstance(result, PlanExplainOut)
        if not validate_plan_explain(result, allowed_names=names, allowed_numbers=numbers):
            _CACHE[cache_key] = dict(fallback)
            return fallback
        explained = {
            "summary": result.summary.strip()[:500],
            "why_order": result.why_order.strip()[:300],
            "what_is_left_out": result.what_is_left_out.strip()[:300],
            "source": "ai",
        }
        _CACHE[cache_key] = dict(explained)
        return explained
    except GatewayError:
        _CACHE[cache_key] = dict(fallback)
        return fallback


def clear_explain_cache() -> None:
    _CACHE.clear()
