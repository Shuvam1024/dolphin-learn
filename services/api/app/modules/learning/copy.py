"""Learner-facing words. The web never invents labels from keys."""

from __future__ import annotations

FACET_LABEL: dict[str, str] = {
    "exposed": "Seen",
    "practicing": "Practicing",
    "independently_demonstrated": "Shown on your own",
    "retained": "Remembered later",
    "self_reported": "Self-reported",
    "unassessed": "Not tried yet",
    "applied": "Applied on a new task",
}

REASON_TEXT: dict[str, str] = {
    "insufficient_minutes": "Not enough minutes this time",
    "prerequisite_deferred": "Comes after a topic that did not fit",
    "skipped_by_learner": "You chose to skip this",
}

PRIORITY_LABEL: dict[str, str] = {
    "understand": "Understand",
    "apply": "Apply",
    "make_it_stick": "Make it stick",
}

PRIORITY_EFFECT: dict[str, str] = {
    "understand": "Fits more topics using the low effort estimate (breadth).",
    "apply": "Fits fewer topics using the high effort estimate so practice can go deeper.",
    "make_it_stick": "Keeps about one fifth of the minutes for later review.",
}

AI_LABEL = "Written by the tutor — check it against the lesson"


def facet_label(facet: str) -> str:
    return FACET_LABEL.get(facet, facet.replace("_", " ").capitalize())


def reason_text(code: str) -> str:
    return REASON_TEXT.get(code, code.replace("_", " "))


def priority_label(priority: str) -> str:
    return PRIORITY_LABEL.get(priority, "Understand")


def priority_effect(priority: str) -> str:
    return PRIORITY_EFFECT.get(priority, PRIORITY_EFFECT["understand"])
