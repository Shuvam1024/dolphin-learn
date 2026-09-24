"""S69: fixture-based evaluation of tutor prompts."""

from __future__ import annotations

from tests.ai_eval import PROMPTS, load_cases, run_all, run_case, write_live_stub


def test_each_prompt_has_twenty_plus_cases() -> None:
    for prompt_id in PROMPTS:
        assert len(load_cases(prompt_id)) >= 20


def test_all_scripted_ai_eval_cases_pass() -> None:
    report = run_all()
    failures = {pid: row["failed"] for pid, row in report.items() if row["failed"]}
    assert failures == {}, failures


def test_ai_eval_live_record_when_requested(monkeypatch) -> None:
    # Always write the scripted report path used before Gate 3; live flag only annotates.
    report = run_all()
    path = write_live_stub(report)
    assert path.exists()
    text = path.read_text()
    assert "hint" in text
    assert "recall_compare" in text
    assert "goal_normalize" in text
    assert "general_outline" in text
    assert "item_draft" in text
    assert "plan_explain" in text
