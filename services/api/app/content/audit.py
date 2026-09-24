"""Publish a content audit markdown report for every competency."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from app.content.loader import DEFAULT_CONTENT_ROOT, errors_only, load_all, validate_all
from app.content.rules import CHECKED_SUBJECTS, GRADED_TYPES

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_AUDIT = REPO_ROOT / "docs" / "evaluations" / "content-audit.md"


def build_audit(root: Path | None = None) -> str:
    content_root = root or DEFAULT_CONTENT_ROOT
    failures = validate_all(content_root)
    errors = errors_only(failures)
    lines = [
        "# Content audit",
        "",
        f"Root: `{content_root}`",
        "",
        f"Errors: **{len(errors)}**",
        "",
    ]
    if errors:
        lines.append("## Errors")
        lines.append("")
        for item in errors:
            lines.append(f"- `{item.path}:{item.line}` [{item.rule}] {item.message}")
        lines.append("")

    lines.append("## Competencies")
    lines.append("")
    for bundle in load_all(content_root):
        for content in bundle.competencies:
            fm = content.frontmatter
            graded = [item for item in content.items if item.type in GRADED_TYPES]
            by_type = Counter(item.type for item in content.items)
            sources = Counter(
                getattr(item, "source", None) or "seed" for item in graded
            )
            difficulties = sorted(
                {
                    item.difficulty
                    for item in graded
                    if item.difficulty is not None
                }
            )
            warnings: list[str] = []
            if bundle.domain.key in CHECKED_SUBJECTS and not content.worked_example_markdown:
                warnings.append("missing worked example")
            if not fm.reviewed_by or not fm.reviewed_on:
                warnings.append("missing review stamp")
            if not any(item.type in GRADED_TYPES for item in content.items):
                warnings.append("no graded items")
            ai_reviewed = sources.get("ai", 0)
            lines.append(f"### `{fm.key}` — {fm.name}")
            lines.append("")
            lines.append(f"- Domain: `{bundle.domain.key}`")
            lines.append(f"- Reviewed: {fm.reviewed_by} on {fm.reviewed_on}")
            lines.append(
                "- Items by type: "
                + ", ".join(f"{key}={count}" for key, count in sorted(by_type.items()))
            )
            lines.append(
                "- Graded sources: "
                + (", ".join(f"{key}={count}" for key, count in sorted(sources.items())) or "none")
            )
            lines.append(
                "- Difficulty spread: "
                + (", ".join(str(item) for item in difficulties) or "n/a")
            )
            if ai_reviewed:
                lines.append(f"- AI-sourced graded items (reviewed): {ai_reviewed}")
            if warnings:
                lines.append("- Warnings: " + "; ".join(warnings))
            else:
                lines.append("- Warnings: none")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.content.audit")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args(argv)
    report = build_audit(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"wrote {args.out}")
    errors = errors_only(validate_all(args.root or DEFAULT_CONTENT_ROOT))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
