"""S86: AI item drafting with reviewer approval before graded use."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from app.config import settings
from app.content.draft_items import draft_for_competency, jaccard, reject_near_duplicates
from app.content.loader import DEFAULT_CONTENT_ROOT, load_all
from app.content.schema import ContentItem, EffortMinutes
from app.db import SessionLocal
from app.modules.ai_gateway.service import get_fake_provider, reset_provider
from app.modules.learning.models import ActivityVersion
from app.seed import seed
from sqlalchemy import select


@pytest.fixture(autouse=True)
def _ai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(settings, "ai_provider", "fake")
    reset_provider()
    fake = get_fake_provider()
    fake.scripts.clear()
    fake.calls.clear()
    yield
    reset_provider()


def test_drafts_land_provisional(tmp_path: Path) -> None:
    # Copy python names into temp root structure
    src = DEFAULT_CONTENT_ROOT / "python"
    dest = tmp_path / "python"
    dest.mkdir()
    for name in ("domain.yaml", "names.md", "names.items.yaml"):
        (dest / name).write_text((src / name).read_text(encoding="utf-8"), encoding="utf-8")
    out = draft_for_competency("python.names", n=2, root=tmp_path)
    assert out is not None
    assert out.name.endswith(".drafts.yaml")
    rows = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert rows
    assert all(row.get("provisional") is True for row in rows)


def test_near_duplicate_rejected() -> None:
    existing = [
        ContentItem(
            id="objective-1",
            type="objective",
            prompt="After the line n = 3, which statement is accurate about binding?",
            choices=["a", "b", "c"],
            answer="b",
            explanation="Binding.",
            difficulty=2,
            effort_minutes=EffortMinutes(low=1, high=2),
        )
    ]
    drafts = [
        {
            "id": "draft-1",
            "type": "objective",
            "prompt": "After the line n = 3, which statement is accurate about binding?",
            "choices": ["a", "b", "c"],
            "answer": "b",
            "explanation": "Binding.",
            "difficulty": 2,
            "effort_minutes": {"low": 1, "high": 2},
        }
    ]
    assert jaccard(existing[0].prompt, drafts[0]["prompt"]) >= 0.8
    kept = reject_near_duplicates(drafts, existing)
    assert kept == []


def test_unreviewed_drafts_not_seeded_as_graded(tmp_path: Path) -> None:
    # Writing drafts next to real content must not change seeded graded rows.
    out = draft_for_competency("python.names", n=1, root=DEFAULT_CONTENT_ROOT)
    assert out is not None and out.exists()
    with SessionLocal() as db:
        seed(db)
        provisional_graded = list(
            db.scalars(
                select(ActivityVersion).where(
                    ActivityVersion.provisional.is_(True),
                    ActivityVersion.activity_type.in_(("objective", "short_answer", "numeric")),
                )
            )
        )
        assert provisional_graded == []
    # Clean up the draft file written beside content
    out.unlink(missing_ok=True)
