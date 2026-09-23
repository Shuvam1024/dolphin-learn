"""S17: seeded Python and math paths include reading and objective items."""

from app.db import SessionLocal
from app.modules.curriculum.models import Domain
from app.modules.learning.models import ActivityVersion
from app.seed import seed
from sqlalchemy import func, select


def test_seed_loads_python_and_math_without_a_model() -> None:
    db = SessionLocal()
    try:
        seed(db)
        seed(db)
        keys = set(db.scalars(select(Domain.key)).all())
        assert {"python", "math"} <= keys
        types = set(db.scalars(select(ActivityVersion.activity_type)).all())
        assert {"reading", "objective"} <= types
        keyed = db.scalar(
            select(func.count())
            .select_from(ActivityVersion)
            .where(ActivityVersion.answer_key.is_not(None))
        )
        assert keyed is not None and keyed >= 2
        lessons = db.scalar(select(func.count()).select_from(ActivityVersion))
        assert lessons is not None and lessons >= 4
    finally:
        db.close()
