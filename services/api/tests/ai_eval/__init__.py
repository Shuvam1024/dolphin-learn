"""Load and run tutor prompt evaluation fixtures (S69)."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

from tests.ai_eval.validators import VALIDATORS

CASES_DIR = Path(__file__).resolve().parent / "cases"
PROMPTS = (
    "hint",
    "explain_differently",
    "misconception_note",
    "recall_compare",
    "goal_normalize",
    "general_outline",
    "item_draft",
    "plan_explain",
)


def load_cases(prompt_id: str) -> list[dict[str, Any]]:
    path = CASES_DIR / f"{prompt_id}.json"
    data = json.loads(path.read_text())
    if not isinstance(data, list) or len(data) < 20:
        raise AssertionError(f"{prompt_id} needs at least 20 fixture cases")
    return data


def run_case(prompt_id: str, case: dict[str, Any]) -> bool:
    validator = VALIDATORS[prompt_id]
    actual = validator(case["inputs"], case["scripted_output"])
    expected = bool(case["expected_validator_result"])
    return actual is expected


def run_all() -> dict[str, dict[str, Any]]:
    report: dict[str, dict[str, Any]] = {}
    for prompt_id in PROMPTS:
        cases = load_cases(prompt_id)
        failures: list[str] = []
        for case in cases:
            if not run_case(prompt_id, case):
                failures.append(str(case.get("id", "?")))
        report[prompt_id] = {
            "total": len(cases),
            "passed": len(cases) - len(failures),
            "failed": failures,
            "pass_rate": (len(cases) - len(failures)) / len(cases),
        }
    return report


def write_live_stub(report: dict[str, dict[str, Any]]) -> Path:
    """Optional live run placeholder — records scripted pass rates, no learner data."""
    docs = Path(__file__).resolve().parents[4] / "docs" / "evaluations"
    docs.mkdir(parents=True, exist_ok=True)
    target = docs / f"ai-eval-{date.today().isoformat()}.md"
    lines = [
        f"# AI eval — {date.today().isoformat()}",
        "",
        "Scripted FakeProvider / validator fixtures (no learner data).",
        "",
    ]
    if os.environ.get("AI_EVAL_LIVE") == "1":
        lines.append("Live provider requested (`AI_EVAL_LIVE=1`); scripted suite still authoritative.")
        lines.append("")
    for prompt_id, row in report.items():
        rate = row["pass_rate"] * 100
        lines.append(f"- **{prompt_id}**: {row['passed']}/{row['total']} ({rate:.0f}%)")
        if row["failed"]:
            lines.append(f"  - failed ids: {', '.join(row['failed'])}")
    lines.append("")
    target.write_text("\n".join(lines))
    return target
