"""Grade a closed-form choice against the versioned key. No model calls."""

from decimal import Decimal


def grade_choice(answer_key: dict[str, str] | None, choice: str) -> tuple[str, Decimal]:
    expected = ""
    if answer_key is not None:
        expected = str(answer_key.get("correct", "")).strip().lower()
    if expected and choice == expected:
        return "correct", Decimal("1.00")
    return "incorrect", Decimal("0.00")


def eligible_for_independent_evidence(assistance: str, outcome: str) -> bool:
    return assistance == "independent" and outcome == "correct"
