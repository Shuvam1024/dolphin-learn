"""S69/S93: fixture-based evaluation and safety suite for every prompt."""

from __future__ import annotations

from tests.ai_eval import PROMPTS, SAFETY_TAGS, load_cases, run_all, run_case, write_live_stub


def test_each_prompt_has_twenty_plus_cases() -> None:
    for prompt_id in PROMPTS:
        assert len(load_cases(prompt_id)) >= 20


def test_each_prompt_covers_safety_tags() -> None:
    """Leakage / injection / overlong / wrong-lang (+ fabricated where relevant)."""
    for prompt_id in PROMPTS:
        ids = " ".join(case["id"] for case in load_cases(prompt_id))
        for tag in SAFETY_TAGS:
            assert tag in ids, f"{prompt_id} missing safety case tag {tag!r}"
        if prompt_id in {"hint", "explain_differently", "misconception_note", "recall_compare", "item_draft", "goal_normalize"}:
            assert "leak" in ids, f"{prompt_id} missing leakage case"
        if prompt_id in {"plan_explain", "general_outline"}:
            assert "fabricated" in ids, f"{prompt_id} missing fabricated-lesson case"


def test_all_scripted_ai_eval_cases_pass() -> None:
    report = run_all()
    failures = {pid: row["failed"] for pid, row in report.items() if row["failed"]}
    assert failures == {}, failures


def test_ai_eval_live_record_when_requested(monkeypatch) -> None:
    # Always write the scripted report path; live flag only annotates.
    report = run_all()
    path = write_live_stub(report)
    assert path.exists()
    text = path.read_text()
    for prompt_id in PROMPTS:
        assert prompt_id in text
