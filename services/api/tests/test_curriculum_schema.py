"""S14: curriculum keys are unique and edges cannot loop onto themselves."""

import uuid

import pytest
from app.db import SessionLocal
from app.modules.curriculum.models import EDGE_REQUIRES, Competency, CompetencyEdge, Domain
from sqlalchemy.exc import IntegrityError


def test_duplicate_domain_and_competency_keys_fail() -> None:
    suffix = uuid.uuid4().hex[:8]
    db = SessionLocal()
    domain = Domain(key=f"python-{suffix}", name="Python")
    db.add(domain)
    db.commit()
    competency = Competency(
        domain_id=domain.id,
        key=f"python.variables-{suffix}",
        name="Variables",
    )
    db.add(competency)
    db.commit()
    try:
        db.add(Domain(key=domain.key, name="Duplicate"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        db.add(
            Competency(domain_id=domain.id, key=competency.key, name="Duplicate skill")
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.close()


def test_self_loop_and_bad_edge_type_fail() -> None:
    suffix = uuid.uuid4().hex[:8]
    db = SessionLocal()
    domain = Domain(key=f"math-{suffix}", name="Math")
    db.add(domain)
    db.commit()
    skill = Competency(domain_id=domain.id, key=f"math.add-{suffix}", name="Addition")
    db.add(skill)
    db.commit()
    try:
        db.add(
            CompetencyEdge(
                from_competency_id=skill.id,
                to_competency_id=skill.id,
                edge_type=EDGE_REQUIRES,
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        other = Competency(domain_id=domain.id, key=f"math.sub-{suffix}", name="Subtraction")
        db.add(other)
        db.commit()
        db.add(
            CompetencyEdge(
                from_competency_id=skill.id,
                to_competency_id=other.id,
                edge_type="GUESS",
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        db.add(
            CompetencyEdge(
                from_competency_id=skill.id,
                to_competency_id=other.id,
                edge_type=EDGE_REQUIRES,
            )
        )
        db.commit()
        db.add(
            CompetencyEdge(
                from_competency_id=skill.id,
                to_competency_id=other.id,
                edge_type=EDGE_REQUIRES,
            )
        )
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.close()
