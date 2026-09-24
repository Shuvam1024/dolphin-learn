"""Purge tombstoned accounts after RETENTION_DAYS (S99)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import settings
from app.db import SessionLocal
from app.modules.ai_gateway.models import AiCall
from app.modules.identity.models import User
from sqlalchemy import select, update


def purge_due_accounts() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(settings.retention_days))
    purged = 0
    with SessionLocal() as db:
        due = list(
            db.scalars(
                select(User).where(User.deleted_at.is_not(None), User.deleted_at <= cutoff)
            )
        )
        for user in due:
            db.execute(
                update(AiCall)
                .where(AiCall.user_id == user.id)
                .values(user_id=None, model="anonymized")
            )
            db.delete(user)
            purged += 1
        db.commit()
    return purged


def main() -> None:
    count = purge_due_accounts()
    print(f"purged {count} account(s)")


if __name__ == "__main__":
    main()
