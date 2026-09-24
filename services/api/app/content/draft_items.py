"""Draft graded items via AI into provisional .drafts.yaml files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from app.content.loader import DEFAULT_CONTENT_ROOT, load_all
from app.content.schema import ContentItem
from app.modules.ai_gateway.service import complete, is_enabled, get_fake_provider

_TOKEN = re.compile(r"[a-z0-9]+", re.I)


class DraftItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    prompt: str
    choices: list[str] | None = None
    answer: str
    explanation: str
    misconceptions: dict[str, str] | None = None
    difficulty: int = Field(ge=1, le=3)
    effort_minutes: dict[str, int]
    provisional: bool = True


class DraftPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DraftItem] = Field(min_length=1, max_length=8)


def _tokens(text: str) -> set[str]:
    return {part.casefold() for part in _TOKEN.findall(text)}


def jaccard(a: str, b: str) -> float:
    left = _tokens(a)
    right = _tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def reject_near_duplicates(
    drafts: list[ContentItem | DraftItem | dict[str, Any]],
    existing: list[ContentItem],
    *,
    threshold: float = 0.8,
) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    prompts = [item.prompt for item in existing]
    for draft in drafts:
        payload = draft if isinstance(draft, dict) else draft.model_dump()
        prompt = str(payload.get("prompt") or "")
        if any(jaccard(prompt, other) >= threshold for other in prompts):
            continue
        if any(jaccard(prompt, str(item.get("prompt") or "")) >= threshold for item in kept):
            continue
        payload["provisional"] = True
        kept.append(payload)
        prompts.append(prompt)
    return kept


def find_competency(root: Path, key: str):
    for bundle in load_all(root):
        for content in bundle.competencies:
            if content.frontmatter.key == key:
                return content, bundle.domain.key
    return None, None


def draft_for_competency(
    competency_key: str,
    *,
    n: int = 4,
    root: Path | None = None,
    write: bool = True,
) -> Path | None:
    content_root = root or DEFAULT_CONTENT_ROOT
    content, domain_key = find_competency(content_root, competency_key)
    if content is None or domain_key is None:
        raise SystemExit(f"unknown competency: {competency_key}")
    existing = [item for item in content.items if item.type in {"objective", "short_answer", "numeric"}]
    variables = {
        "competency_key": competency_key,
        "reading": content.reading_markdown[:3000],
        "existing_prompts": [item.prompt for item in existing][:20],
        "n": n,
    }
    if not is_enabled(None, None):
        # Deterministic stub for offline CI when AI is off — still provisional.
        raw_items = [
            {
                "id": f"draft-objective-{index}",
                "type": "objective",
                "prompt": (
                    f"Draft practice {index} for {competency_key}: which idea fits the reading?\n\n"
                    "a) A distractor that mismatches the reading\n"
                    "b) The idea that matches the reading\n"
                    "c) An unrelated idea"
                ),
                "choices": [
                    "A distractor that mismatches the reading",
                    "The idea that matches the reading",
                    "An unrelated idea",
                ],
                "answer": "b",
                "explanation": "The reading supports the matching idea.",
                "misconceptions": {"a": "That mismatches the reading.", "c": "Unrelated."},
                "difficulty": 1 + (index % 3),
                "effort_minutes": {"low": 2, "high": 4},
                "provisional": True,
            }
            for index in range(1, n + 1)
        ]
    else:
        raw = complete(None, None, "item_draft", variables, DraftPayload)
        assert isinstance(raw, DraftPayload)
        raw_items = [item.model_dump() for item in raw.items[:n]]

    # Validate shape through ContentItem where possible
    validated: list[ContentItem] = []
    for row in raw_items:
        row = dict(row)
        row.pop("provisional", None)
        validated.append(ContentItem.model_validate(row))

    kept = reject_near_duplicates(validated, existing)
    if not kept:
        raise SystemExit("all drafts rejected as near-duplicates")

    out = content_root / domain_key / f"{competency_key.split('.', 1)[-1]}.drafts.yaml"
    # Prefer full key stem for nested keys like fractions.parts
    stem = competency_key.split(".", 1)[-1].replace(".", "_")
    # Match existing file naming (names.md → names.drafts.yaml)
    md_candidates = list((content_root / domain_key).glob("*.md"))
    for path in md_candidates:
        text = path.read_text(encoding="utf-8")
        if f"key: {competency_key}" in text or f"key: '{competency_key}'" in text:
            out = path.with_suffix(".drafts.yaml")
            break
    else:
        out = content_root / domain_key / f"{stem}.drafts.yaml"

    if write:
        out.write_text(
            yaml.safe_dump(kept, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.content.draft_items")
    parser.add_argument("--competency", required=True)
    parser.add_argument("--n", type=int, default=4)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)
    path = draft_for_competency(args.competency, n=args.n, root=args.root)
    print(f"wrote provisional drafts: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
