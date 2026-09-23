"""Load the reviewed Python and math mini-curricula. Idempotent. No model calls."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.modules.curriculum.models import EDGE_REQUIRES, Competency, CompetencyEdge, Domain
from app.modules.learning.models import ActivityVersion, Lesson


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
        ),
        requires=(("python.calls", "python.names"),),
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
                    db.add(
                        ActivityVersion(
                            lesson_id=lesson.id,
                            version=activity.version,
                            activity_type=activity.activity_type,
                            prompt=activity.prompt,
                            answer_key=activity.answer_key,
                            effort_minutes_low=activity.effort_low,
                            effort_minutes_high=activity.effort_high,
                        )
                    )
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed(db)
    print("seeded python and math mini-curricula")


if __name__ == "__main__":
    main()
