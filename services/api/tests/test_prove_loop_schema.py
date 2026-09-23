"""S16: Prove Loop tables import, migrate, and keep ownership foreign keys."""

from app.modules.learning.models import (
    Attempt,
    CompetencyEvidence,
    CompetencyState,
    LearningPath,
    LearningSession,
    ReviewEvent,
    ReviewItem,
)


def _fk_tables(model: type) -> set[str]:
    return {fk.column.table.name for fk in model.__table__.foreign_keys}


def test_ownership_foreign_keys_are_present() -> None:
    assert "users" in _fk_tables(LearningPath)
    assert "goals" in _fk_tables(LearningPath)
    assert "users" in _fk_tables(LearningSession)
    assert "users" in _fk_tables(Attempt)
    assert "activity_versions" in _fk_tables(Attempt)
    assert "users" in _fk_tables(CompetencyEvidence)
    assert "users" in _fk_tables(CompetencyState)
    assert "users" in _fk_tables(ReviewItem)
    assert "review_items" in _fk_tables(ReviewEvent)
    assert "updated_at" not in Attempt.__table__.columns
    assert "updated_at" not in ReviewEvent.__table__.columns
