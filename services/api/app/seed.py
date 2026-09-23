"""Load the reviewed Python and math mini-curricula. Idempotent. No model calls."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.modules.curriculum.models import EDGE_REQUIRES, Competency, CompetencyEdge, Domain
from app.modules.learning.models import ActivityVersion, Lesson

_CHOICE_LINE = re.compile(r"^([a-c])\)\s*(.*)$", re.IGNORECASE)


def _choices_from_prompt(prompt: str) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for raw in prompt.splitlines():
        line = raw.strip()
        match = _CHOICE_LINE.match(line)
        if match:
            found.append({"id": match.group(1).lower(), "label": match.group(2).strip() or line})
    return found


@dataclass(frozen=True)
class ActivitySpec:
    version: int
    activity_type: str
    prompt: str
    answer_key: dict[str, str] | None
    effort_low: int
    effort_high: int


@dataclass(frozen=True)
class LessonSpec:
    key: str
    title: str
    body: str
    competency_key: str
    activities: tuple[ActivitySpec, ...]


@dataclass(frozen=True)
class CompetencySpec:
    key: str
    name: str


@dataclass(frozen=True)
class DomainSpec:
    key: str
    name: str
    competencies: tuple[CompetencySpec, ...]
    requires: tuple[tuple[str, str], ...]
    lessons: tuple[LessonSpec, ...]


CURRICULA: tuple[DomainSpec, ...] = (
    DomainSpec(
        key="python",
        name="Python",
        competencies=(
            CompetencySpec("python.names", "Names and values"),
            CompetencySpec("python.calls", "Calling a function"),
            CompetencySpec("python.conditionals", "Choosing with if"),
        ),
        requires=(
            ("python.calls", "python.names"),
            ("python.conditionals", "python.names"),
        ),
        lessons=(
            LessonSpec(
                key="python.names.intro",
                title="Names point at values",
                competency_key="python.names",
                body=(
                    "In Python, `n = 3` does not create a box that permanently holds 3. "
                    "It binds the name `n` to the value `3`. Later, `n = n + 1` looks up "
                    "the current value, adds one, and rebinds the name."
                ),
                activities=(
                    ActivitySpec(
                        1,
                        "reading",
                        "Read the short note on names and values. You are not scored for reading.",
                        None,
                        5,
                        8,
                    ),
                    ActivitySpec(
                        2,
                        "objective",
                        (
                            "After the line `n = 3`, which statement is accurate?\n\n"
                            "a) `n` is a permanent box that can only hold 3\n"
                            "b) The name `n` is bound to the value 3\n"
                            "c) `n` is a function call"
                        ),
                        {"correct": "b"},
                        3,
                        5,
                    ),
                    ActivitySpec(
                        3,
                        "objective",
                        (
                            "What does `n = n + 1` do when `n` was bound to 3?\n\n"
                            "a) It rebinds `n` to 4\n"
                            "b) It deletes the name `n`\n"
                            "c) It calls a function named n"
                        ),
                        {"correct": "a"},
                        1,
                        2,
                    ),
                    ActivitySpec(
                        4,
                        "objective",
                        (
                            "Which line only looks up a name and does not bind one?\n\n"
                            "a) `n = 3`\n"
                            "b) `print(n)`\n"
                            "c) `n = 4`"
                        ),
                        {"correct": "b"},
                        1,
                        2,
                    ),
                ),
            ),
            LessonSpec(
                key="python.calls.intro",
                title="Call a function by name",
                competency_key="python.calls",
                body=(
                    "A call looks up a function by name and runs it. `print(n)` looks up "
                    "`print`, passes the current value of `n`, and does not bind a new name "
                    "unless you write an assignment."
                ),
                activities=(
                    ActivitySpec(
                        1,
                        "reading",
                        "Read the note on calling a function. You are not scored for reading.",
                        None,
                        20,
                        40,
                    ),
                    ActivitySpec(
                        2,
                        "objective",
                        (
                            "Which line calls a function?\n\n"
                            "a) `n = 3`\n"
                            "b) `print(n)`\n"
                            "c) `n`"
                        ),
                        {"correct": "b"},
                        15,
                        25,
                    ),
                ),
            ),
            LessonSpec(
                key="python.conditionals.intro",
                title="Choose a branch with if",
                competency_key="python.conditionals",
                body=(
                    "An `if` statement checks a condition. When the condition is true, "
                    "Python runs the indented block under `if`. When it is false, that "
                    "block is skipped. An optional `else` runs only when the condition "
                    "was false. The condition is an expression that evaluates to true "
                    "or false; it does not permanently change a name unless you also "
                    "write an assignment."
                ),
                activities=(
                    ActivitySpec(
                        1,
                        "reading",
                        "Read the note on if and else. You are not scored for reading.",
                        None,
                        8,
                        12,
                    ),
                    ActivitySpec(
                        2,
                        "objective",
                        (
                            "Given `n = 3` and `if n > 2: print(\"big\")`, what happens?\n\n"
                            "a) Nothing prints because if never runs print\n"
                            "b) `print(\"big\")` runs because the condition is true\n"
                            "c) Python rebinds `n` to True"
                        ),
                        {"correct": "b"},
                        4,
                        6,
                    ),
                    ActivitySpec(
                        3,
                        "objective",
                        (
                            "Given `n = 1` and this program:\n\n"
                            "```\n"
                            "if n > 2:\n"
                            '    print("big")\n'
                            "else:\n"
                            '    print("small")\n'
                            "```\n\n"
                            "What prints?\n\n"
                            "a) big\n"
                            "b) small\n"
                            "c) both big and small"
                        ),
                        {"correct": "b"},
                        4,
                        6,
                    ),
                    ActivitySpec(
                        4,
                        "objective",
                        (
                            "Which line is a condition, not an assignment?\n\n"
                            "a) `n = 3`\n"
                            "b) `n > 2`\n"
                            "c) `print(n)`"
                        ),
                        {"correct": "b"},
                        3,
                        5,
                    ),
                ),
            ),
        ),
    ),
    DomainSpec(
        key="math",
        name="Foundational math",
        competencies=(
            CompetencySpec("math.fractions.parts", "A fraction as parts of a whole"),
            CompetencySpec("math.fractions.add", "Add fractions with the same denominator"),
        ),
        requires=(("math.fractions.add", "math.fractions.parts"),),
        lessons=(
            LessonSpec(
                key="math.fractions.parts.intro",
                title="Parts of one whole",
                competency_key="math.fractions.parts",
                body=(
                    "The fraction 3/4 means three parts out of four equal parts of one whole. "
                    "The denominator names the size of each part. The numerator counts how "
                    "many of those parts you have. Adding fractions with the same denominator "
                    "means adding the numerators and keeping the denominator."
                ),
                activities=(
                    ActivitySpec(
                        1,
                        "reading",
                        "Read the note on numerators and denominators.",
                        None,
                        5,
                        8,
                    ),
                    ActivitySpec(
                        2,
                        "objective",
                        (
                            "What is 1/4 + 2/4?\n\n"
                            "a) 3/8\n"
                            "b) 3/4\n"
                            "c) 2/4"
                        ),
                        {"correct": "b"},
                        3,
                        5,
                    ),
                ),
            ),
        ),
    ),
    DomainSpec(
        key="software",
        name="Software practice",
        competencies=(
            CompetencySpec("software.failing_test", "Read a failing test"),
            CompetencySpec("software.bug_name", "Name what the test caught"),
        ),
        requires=(("software.bug_name", "software.failing_test"),),
        lessons=(
            LessonSpec(
                key="software.failing_test.intro",
                title="A failing test is a claim",
                competency_key="software.failing_test",
                body=(
                    "A failing automated test is a claim about the program that did not hold. "
                    "Read the test name and the assertion first. They say what should be true. "
                    "The stack or failure message says what was true instead. You are not "
                    "running code here; you are reading what the check expected."
                ),
                activities=(
                    ActivitySpec(
                        1,
                        "reading",
                        "Read the note on failing tests. You are not scored for reading.",
                        None,
                        6,
                        10,
                    ),
                    ActivitySpec(
                        2,
                        "objective",
                        (
                            "A test named `adds_two_numbers` fails with "
                            "`expected 5, got 4`. What should you read first?\n\n"
                            "a) Only the production code, and ignore the test name\n"
                            "b) The test name and the assertion that expected 5\n"
                            "c) A random line from a different file"
                        ),
                        {"correct": "b"},
                        4,
                        6,
                    ),
                    ActivitySpec(
                        3,
                        "objective",
                        (
                            "What does a failing test claim?\n\n"
                            "a) That the learner has mastered the topic\n"
                            "b) That some expected condition about the program did not hold\n"
                            "c) That the calendar date is a study deadline"
                        ),
                        {"correct": "b"},
                        3,
                        5,
                    ),
                ),
            ),
            LessonSpec(
                key="software.bug_name.intro",
                title="Name the mismatch",
                competency_key="software.bug_name",
                body=(
                    "After you read the failing claim, name the mismatch in plain words: "
                    "what was expected, and what happened. A clear name helps you fix the "
                    "right thing. Do not award yourself mastery for guessing; wait for a "
                    "check that asks you to identify the mismatch."
                ),
                activities=(
                    ActivitySpec(
                        1,
                        "reading",
                        "Read the note on naming the mismatch. You are not scored for reading.",
                        None,
                        8,
                        12,
                    ),
                    ActivitySpec(
                        2,
                        "objective",
                        (
                            "The test expected the list `[1, 2]` but got `[2, 1]`. "
                            "Which plain description fits?\n\n"
                            "a) The items are present but in the wrong order\n"
                            "b) The program crashed before returning\n"
                            "c) The test never ran"
                        ),
                        {"correct": "a"},
                        5,
                        8,
                    ),
                    ActivitySpec(
                        3,
                        "objective",
                        (
                            "Why name the mismatch before changing code?\n\n"
                            "a) So you fix the behavior the test actually checked\n"
                            "b) So the product can invent a mastery percent\n"
                            "c) So a calendar deadline becomes study time"
                        ),
                        {"correct": "a"},
                        4,
                        6,
                    ),
                ),
            ),
        ),
    ),
)


def _domain(db: Session, spec: DomainSpec) -> Domain:
    found = db.scalar(select(Domain).where(Domain.key == spec.key))
    if found is not None:
        return found
    found = Domain(key=spec.key, name=spec.name)
    db.add(found)
    db.flush()
    return found


def _competency(db: Session, domain: Domain, spec: CompetencySpec) -> Competency:
    found = db.scalar(select(Competency).where(Competency.key == spec.key))
    if found is not None:
        return found
    found = Competency(domain_id=domain.id, key=spec.key, name=spec.name)
    db.add(found)
    db.flush()
    return found


def seed(db: Session) -> None:
    for domain_spec in CURRICULA:
        domain = _domain(db, domain_spec)
        by_key = {
            spec.key: _competency(db, domain, spec) for spec in domain_spec.competencies
        }
        for source_key, target_key in domain_spec.requires:
            source = by_key[source_key]
            target = by_key[target_key]
            exists = db.scalar(
                select(CompetencyEdge).where(
                    CompetencyEdge.from_competency_id == source.id,
                    CompetencyEdge.to_competency_id == target.id,
                    CompetencyEdge.edge_type == EDGE_REQUIRES,
                )
            )
            if exists is None:
                db.add(
                    CompetencyEdge(
                        from_competency_id=source.id,
                        to_competency_id=target.id,
                        edge_type=EDGE_REQUIRES,
                    )
                )
        for lesson_spec in domain_spec.lessons:
            lesson = db.scalar(select(Lesson).where(Lesson.key == lesson_spec.key))
            if lesson is None:
                lesson = Lesson(
                    competency_id=by_key[lesson_spec.competency_key].id,
                    key=lesson_spec.key,
                    title=lesson_spec.title,
                    body_markdown=lesson_spec.body,
                )
                db.add(lesson)
                db.flush()
            for activity in lesson_spec.activities:
                found = db.scalar(
                    select(ActivityVersion).where(
                        ActivityVersion.lesson_id == lesson.id,
                        ActivityVersion.version == activity.version,
                    )
                )
                if found is None:
                    choices = _choices_from_prompt(activity.prompt)
                    db.add(
                        ActivityVersion(
                            lesson_id=lesson.id,
                            version=activity.version,
                            item_id=f"{activity.activity_type}-{activity.version}",
                            activity_type=activity.activity_type,
                            prompt=activity.prompt,
                            answer_key=activity.answer_key,
                            payload={"choices": choices} if choices else {},
                            provisional=False,
                            source="seed",
                            reviewed_at=datetime.now(timezone.utc),
                            effort_minutes_low=activity.effort_low,
                            effort_minutes_high=activity.effort_high,
                        )
                    )
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed(db)
    print("seeded python, math, and software mini-curricula")


if __name__ == "__main__":
    main()
