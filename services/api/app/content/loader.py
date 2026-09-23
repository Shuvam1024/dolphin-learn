"""Load and validate curricula from the repo `content/` tree."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.content.rules import RuleFailure, validate_domain
from app.content.schema import (
    CompetencyContent,
    CompetencyFrontmatter,
    ContentItem,
    DomainContent,
    DomainFile,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONTENT_ROOT = REPO_ROOT / "content"


def _parse_frontmatter(text: str) -> tuple[dict[str, object], str, int]:
    if not text.startswith("---"):
        raise ValueError("Missing frontmatter opener")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Frontmatter not closed")
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    # body starts after second ---; approximate line offset
    fm_lines = parts[1].count("\n") + 2
    return meta, body, fm_lines


def _section(body: str, heading: str) -> str | None:
    marker = f"## {heading}"
    if marker not in body:
        return None
    after = body.split(marker, 1)[1]
    # stop at next ## heading
    chunks = after.split("\n## ")
    return chunks[0].strip()


def _load_competency(path: Path, body_line_offset: int = 0) -> CompetencyContent:
    text = path.read_text(encoding="utf-8")
    meta, body, fm_line_offset = _parse_frontmatter(text)
    frontmatter = CompetencyFrontmatter.model_validate(meta)
    reading = _section(body, "Reading")
    if reading is None:
        raise ValueError(f"{path}: missing ## Reading")
    worked = _section(body, "Worked example")
    items_path = path.with_suffix(".items.yaml")
    if not items_path.is_file():
        raise ValueError(f"Missing items file: {items_path}")
    raw_items = yaml.safe_load(items_path.read_text(encoding="utf-8")) or []
    items = [ContentItem.model_validate(row) for row in raw_items]
    line_map = {
        "domain": 2,
        "requires": 3,
        "reading": fm_line_offset + 1,
        "items": 1,
    }
    for index, item in enumerate(items, start=1):
        line_map[f"item:{item.id}"] = index
    return CompetencyContent(
        path=str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path),
        frontmatter=frontmatter,
        reading_markdown=reading,
        worked_example_markdown=worked,
        items=items,
        line_map=line_map,
    )


def load_domain(domain_dir: Path) -> DomainContent:
    domain_file = domain_dir / "domain.yaml"
    domain = DomainFile.model_validate(yaml.safe_load(domain_file.read_text(encoding="utf-8")))
    competencies: list[CompetencyContent] = []
    for md_path in sorted(domain_dir.glob("*.md")):
        competencies.append(_load_competency(md_path))
    return DomainContent(domain=domain, competencies=competencies)


def load_all(content_root: Path | None = None) -> list[DomainContent]:
    root = content_root or DEFAULT_CONTENT_ROOT
    domains: list[DomainContent] = []
    for domain_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if not (domain_dir / "domain.yaml").is_file():
            continue
        domains.append(load_domain(domain_dir))
    return domains


def validate_all(content_root: Path | None = None) -> list[RuleFailure]:
    failures: list[RuleFailure] = []
    for domain in load_all(content_root):
        failures.extend(validate_domain(domain))
    return failures
