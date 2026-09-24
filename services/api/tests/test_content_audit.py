"""S89: content checklist enforcement and audit publication."""

from pathlib import Path

from app.content.audit import build_audit
from app.content.loader import DEFAULT_CONTENT_ROOT, errors_only, validate_all
from app.content.rules import RuleFailure


def test_audit_lists_competencies_with_zero_errors() -> None:
    failures = errors_only(validate_all())
    assert failures == []
    report = build_audit()
    assert "Errors: **0**" in report
    assert "`python.names`" in report
    assert "AI-sourced graded items (reviewed)" in report


def test_unreviewed_fixture_fails_validation(tmp_path: Path) -> None:
    import shutil

    root = tmp_path / "content"
    shutil.copytree(DEFAULT_CONTENT_ROOT, root)
    names = root / "python" / "names.md"
    text = names.read_text(encoding="utf-8")
    text = text.replace("reviewed_by: curriculum", "reviewed_by: ''")
    names.write_text(text, encoding="utf-8")
    failures = errors_only(validate_all(root))
    assert any(item.rule == "review_stamp_required" for item in failures)
