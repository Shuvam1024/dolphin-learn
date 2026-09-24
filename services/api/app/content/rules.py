"""Validation rules for curriculum files. Failures carry path and line."""

from __future__ import annotations

from dataclasses import dataclass

from app.content.schema import ContentItem, DomainContent

GRADED_TYPES = frozenset({"objective", "short_answer", "numeric"})


@dataclass(frozen=True)
class RuleFailure:
    path: str
    line: int
    rule: str
    message: str


def _words(text: str) -> int:
    return len([part for part in text.split() if part.strip()])


def _has_cycle(edges: dict[str, list[str]]) -> bool:
    visiting: set[str] = set()
    seen: set[str] = set()

    def walk(node: str) -> bool:
        if node in visiting:
            return True
        if node in seen:
            return False
        visiting.add(node)
        for nxt in edges.get(node, []):
            if walk(nxt):
                return True
        visiting.remove(node)
        seen.add(node)
        return False

    return any(walk(node) for node in edges)


def _prompt_contains_answer(item: ContentItem) -> bool:
    if not item.answer:
        return False
    answer = item.answer.strip()
    if not answer:
        return False
    stem = item.prompt
    correct_label = ""
    if item.choices:
        lines = item.prompt.splitlines()
        stem_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            lower = stripped.lower()
            if lower.startswith(("a)", "b)", "c)", "d)")):
                letter = lower[0]
                if letter == answer.casefold() and len(answer) == 1:
                    correct_label = stripped[2:].strip()
                continue
            if correct_label:
                # already past choices; ignore trailing notes
                continue
            stem_lines.append(line)
        stem = "\n".join(stem_lines)
        if len(answer) == 1 and answer.isalpha():
            if not correct_label:
                return False
            return correct_label.casefold() in stem.casefold()
    return answer.casefold() in stem.casefold()


def validate_domain(bundle: DomainContent) -> list[RuleFailure]:
    failures: list[RuleFailure] = []
    keys = [item.frontmatter.key for item in bundle.competencies]
    if len(keys) != len(set(keys)):
        failures.append(
            RuleFailure(bundle.domain.key, 1, "unique_competency_keys", "Duplicate competency keys")
        )

    known = set(keys)
    edges: dict[str, list[str]] = {key: [] for key in keys}

    for competency in bundle.competencies:
        fm = competency.frontmatter
        path = competency.path
        if fm.domain != bundle.domain.key:
            failures.append(
                RuleFailure(
                    path,
                    competency.line_map.get("domain", 1),
                    "domain_match",
                    f"Frontmatter domain {fm.domain!r} does not match folder {bundle.domain.key!r}",
                )
            )
        for req in fm.requires:
            line = competency.line_map.get("requires", 1)
            if req not in known:
                failures.append(
                    RuleFailure(path, line, "requires_exist", f"Unknown requires target {req!r}")
                )
            else:
                edges[fm.key].append(req)

        reading_words = _words(competency.reading_markdown)
        if reading_words < 80 or reading_words > 400:
            failures.append(
                RuleFailure(
                    path,
                    competency.line_map.get("reading", 1),
                    "reading_length",
                    f"Reading must be 80–400 words (found {reading_words})",
                )
            )

        graded = [item for item in competency.items if item.type in GRADED_TYPES]
        if len(graded) < 3:
            failures.append(
                RuleFailure(
                    path,
                    competency.line_map.get("items", 1),
                    "graded_count",
                    f"Need ≥ 3 graded items (found {len(graded)})",
                )
            )

        seen_ids: set[str] = set()
        for item in competency.items:
            item_line = competency.line_map.get(
                f"item:{item.id}", competency.line_map.get("items", 1)
            )
            if item.id in seen_ids:
                failures.append(
                    RuleFailure(path, item_line, "unique_ids", f"Duplicate item id {item.id!r}")
                )
            seen_ids.add(item.id)
            if item.effort_minutes.high < item.effort_minutes.low:
                failures.append(
                    RuleFailure(path, item_line, "effort_order", "effort high must be ≥ low")
                )
            if item.effort_minutes.high > 120:
                failures.append(
                    RuleFailure(
                        path, item_line, "effort_realistic",
                        "effort high above 120 minutes",
                    )
                )
            if item.type in GRADED_TYPES:
                if item.difficulty is None:
                    failures.append(
                        RuleFailure(
                            path, item_line, "difficulty_present",
                            "Graded items need difficulty",
                        )
                    )
                if not (item.explanation and item.explanation.strip()):
                    failures.append(
                        RuleFailure(
                            path, item_line, "explanation_required",
                            "Graded items need explanation",
                        )
                    )
                if item.type == "objective":
                    notes = item.misconceptions
                    count = 0
                    if isinstance(notes, dict):
                        count = sum(1 for value in notes.values() if str(value).strip())
                    elif isinstance(notes, list):
                        count = sum(1 for value in notes if str(value).strip())
                    if count < 1:
                        failures.append(
                            RuleFailure(
                                path,
                                item_line,
                                "misconception_required",
                                "Objective items need at least one misconception note",
                            )
                        )
                if _prompt_contains_answer(item):
                    failures.append(
                        RuleFailure(
                            path,
                            item_line,
                            "prompt_hides_answer",
                            "Prompt stem must not contain its answer",
                        )
                    )
            if item.type == "objective" and (not item.choices or len(item.choices) < 2):
                failures.append(
                    RuleFailure(
                        path, item_line, "objective_choices",
                        "Objective items need choices",
                    )
                )

    if _has_cycle(edges):
        failures.append(
            RuleFailure(
                f"content/{bundle.domain.key}/domain.yaml",
                1,
                "no_cycles",
                "Competency requires graph has a cycle",
            )
        )
    return failures
