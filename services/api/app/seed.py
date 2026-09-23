"""Load reviewed curricula from `content/` into the database. Idempotent. No model calls."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.loader import load_all, validate_all
from app.content.schema import CompetencyContent, ContentItem
from app.db import SessionLocal
from app.modules.curriculum.models import EDGE_REQUIRES, Competency, CompetencyEdge, Domain
from app.modules.learning.models import ActivityVersion, Lesson


def _domain(db: Session, key: str, name: str) -> Domain:
    found = db.scalar(select(Domain).where(Domain.key == key))
    if found is not None:
        if found.name != name:
            found.name = name
        return found
    found = Domain(key=key, name=name)
    db.add(found)
    db.flush()
    return found


def _competency(db: Session, domain: Domain, key: str, name: str) -> Competency:
    found = db.scalar(select(Competency).where(Competency.key == key))
    if found is not None:
        if found.name != name:
            found.name = name
        return found
    found = Competency(domain_id=domain.id, key=key, name=name)
    db.add(found)
    db.flush()
    return found


def _payload_for(item: ContentItem) -> dict[str, object]:
    if item.type == "objective" and item.choices:
        return {
            "choices": [
                {"id": "abc"[index], "label": label}
                for index, label in enumerate(item.choices)
                if index < 3
            ]
        }
    if item.type == "short_answer":
        return {
            "alternates": list(item.alternates or []),
            "normalize": ["strip", "lower"],
        }
    if item.type == "numeric":
        return {
            "tolerance": item.tolerance if item.tolerance is not None else 0,
            "accept_fractions": True,
        }
    if item.type == "free_recall":
        return {"reveal_lesson": True}
    if item.type == "worked_example":
        return {"body_markdown": item.prompt}
    return {}


def _version_number(item_id: str, index: int) -> int:
    parts = item_id.rsplit("-", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return index


def _upsert_lesson(
    db: Session,
    competency: Competency,
    content: CompetencyContent,
) -> Lesson:
    lesson_key = f"{content.frontmatter.key}.intro"
    lesson = db.scalar(select(Lesson).where(Lesson.key == lesson_key))
    reviewed_at = datetime.fromisoformat(content.frontmatter.reviewed_on).replace(
        tzinfo=timezone.utc
    )
    if lesson is None:
        lesson = Lesson(
            competency_id=competency.id,
            key=lesson_key,
            title=content.frontmatter.lesson_title,
            body_markdown=content.reading_markdown,
            provisional=False,
            source="seed",
        )
        db.add(lesson)
        db.flush()
    else:
        lesson.title = content.frontmatter.lesson_title
        lesson.body_markdown = content.reading_markdown
        lesson.provisional = False
        lesson.source = "seed"

    if content.worked_example_markdown:
        # Worked example activity is added from items when present; body lives on payload.
        pass

    for index, item in enumerate(content.items, start=1):
        version_number = _version_number(item.id, index)
        found = db.scalar(
            select(ActivityVersion).where(
                ActivityVersion.lesson_id == lesson.id,
                ActivityVersion.item_id == item.id,
            )
        )
        answer_key = {"correct": item.answer} if item.answer else None
        payload = _payload_for(item)
        if item.type == "worked_example" and content.worked_example_markdown:
            payload = {"body_markdown": content.worked_example_markdown}
        if found is None:
            db.add(
                ActivityVersion(
                    lesson_id=lesson.id,
                    version=version_number,
                    item_id=item.id,
                    activity_type=item.type,
                    prompt=item.prompt,
                    answer_key=answer_key,
                    explanation=item.explanation,
                    misconceptions=item.misconceptions,  # type: ignore[arg-type]
                    payload=payload,
                    provisional=False,
                    source="seed",
                    reviewed_at=reviewed_at,
                    effort_minutes_low=item.effort_minutes.low,
                    effort_minutes_high=item.effort_minutes.high,
                )
            )
        else:
            found.version = version_number
            found.activity_type = item.type
            found.prompt = item.prompt
            found.answer_key = answer_key
            found.explanation = item.explanation
            found.misconceptions = item.misconceptions  # type: ignore[assignment]
            found.payload = payload
            found.provisional = False
            found.source = "seed"
            found.reviewed_at = reviewed_at
            found.effort_minutes_low = item.effort_minutes.low
            found.effort_minutes_high = item.effort_minutes.high
    return lesson


def seed(db: Session) -> None:
    failures = validate_all()
    if failures:
        details = "; ".join(f"{item.path}:{item.line} {item.rule}" for item in failures[:5])
        raise RuntimeError(f"content validation failed: {details}")

    for domain_content in load_all():
        domain = _domain(db, domain_content.domain.key, domain_content.domain.name)
        by_key = {
            item.frontmatter.key: _competency(
                db, domain, item.frontmatter.key, item.frontmatter.name
            )
            for item in domain_content.competencies
        }
        for content in domain_content.competencies:
            competency = by_key[content.frontmatter.key]
            for req in content.frontmatter.requires:
                source = by_key[content.frontmatter.key]
                target = by_key[req]
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
            _upsert_lesson(db, competency, content)
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed(db)
    print("seeded curricula from content/")


if __name__ == "__main__":
    main()
