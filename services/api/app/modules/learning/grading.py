"""Deterministic graders for choice, short answer, and numeric. No model calls."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from app.modules.learning.models import ActivityVersion

_TERMINAL_PUNCT = re.compile(r"[.!?…]+$")
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class GradeResult:
    outcome: str
    score: Decimal
    evaluator: str = "deterministic"


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value)
    text = text.casefold()
    text = _WHITESPACE.sub(" ", text).strip()
    text = _TERMINAL_PUNCT.sub("", text).strip()
    return text


def parse_number(value: str) -> Decimal | None:
    raw = unicodedata.normalize("NFKC", value).strip().casefold()
    if not raw:
        return None
    raw = raw.replace(",", "")
    mixed = re.fullmatch(r"(-?\d+)\s+(\d+)\s*/\s*(\d+)", raw)
    if mixed:
        whole, num, den = mixed.groups()
        try:
            return Decimal(whole) + (Decimal(num) / Decimal(den))
        except (InvalidOperation, ZeroDivisionError):
            return None
    fraction = re.fullmatch(r"(-?\d+)\s*/\s*(-?\d+)", raw)
    if fraction:
        num, den = fraction.groups()
        try:
            return Decimal(num) / Decimal(den)
        except (InvalidOperation, ZeroDivisionError):
            return None
    if raw.startswith("."):
        raw = f"0{raw}"
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def grade_choice(answer_key: dict[str, str] | None, choice: str) -> tuple[str, Decimal]:
    result = grade_objective(answer_key, choice)
    return result.outcome, result.score


def grade_objective(answer_key: dict[str, str] | None, choice: str) -> GradeResult:
    expected = ""
    if answer_key is not None:
        expected = str(answer_key.get("correct", "")).strip().lower()
    if expected and choice.strip().lower() == expected:
        return GradeResult("correct", Decimal("1.00"))
    return GradeResult("incorrect", Decimal("0.00"))


def grade_short_answer(activity: ActivityVersion, text: str) -> GradeResult:
    if not text.strip():
        return GradeResult("incorrect", Decimal("0.00"))
    expected = ""
    if activity.answer_key is not None:
        expected = str(activity.answer_key.get("correct", ""))
    candidates = [expected]
    payload = activity.payload or {}
    alternates = payload.get("alternates") if isinstance(payload, dict) else None
    if isinstance(alternates, list):
        candidates.extend(str(item) for item in alternates)
    normalized = normalize_text(text)
    for candidate in candidates:
        if candidate and normalize_text(candidate) == normalized:
            return GradeResult("correct", Decimal("1.00"))
    return GradeResult("incorrect", Decimal("0.00"))


def grade_numeric(activity: ActivityVersion, value: str) -> GradeResult:
    if not value.strip():
        return GradeResult("incorrect", Decimal("0.00"))
    actual = parse_number(value)
    if actual is None:
        return GradeResult("incorrect", Decimal("0.00"))
    expected_raw = ""
    if activity.answer_key is not None:
        expected_raw = str(activity.answer_key.get("correct", ""))
    expected = parse_number(expected_raw)
    if expected is None:
        return GradeResult("incorrect", Decimal("0.00"))
    tolerance = Decimal("0")
    payload = activity.payload or {}
    if isinstance(payload, dict) and payload.get("tolerance") is not None:
        try:
            tolerance = Decimal(str(payload["tolerance"]))
        except InvalidOperation:
            tolerance = Decimal("0")
    if abs(actual - expected) <= tolerance:
        return GradeResult("correct", Decimal("1.00"))
    return GradeResult("incorrect", Decimal("0.00"))


def grade(activity: ActivityVersion, response: dict[str, Any]) -> GradeResult:
    kind = activity.activity_type
    if kind == "objective":
        return grade_objective(activity.answer_key, str(response.get("choice", "")))
    if kind == "short_answer":
        return grade_short_answer(activity, str(response.get("text", "")))
    if kind == "numeric":
        return grade_numeric(activity, str(response.get("value", "")))
    return GradeResult("incorrect", Decimal("0.00"))


def eligible_for_independent_evidence(assistance: str, outcome: str) -> bool:
    return assistance == "independent" and outcome == "correct"
