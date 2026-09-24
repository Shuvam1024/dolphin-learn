"""Access-token revocation (logout). Opaque jti only — no password store."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db import Base
from sqlalchemy import DateTime, ForeignKey, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column


class AuthRevocation(Base):
    __tablename__ = "auth_revocations"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def is_revoked(db: Session, jti: str) -> bool:
    row = db.get(AuthRevocation, jti)
    if row is None:
        return False
    if row.expires_at <= datetime.now(timezone.utc):
        return False
    return True


def revoke_jti(
    db: Session,
    *,
    jti: str,
    expires_at: datetime,
    user_id: uuid.UUID | None = None,
) -> AuthRevocation:
    existing = db.get(AuthRevocation, jti)
    if existing is not None:
        return existing
    row = AuthRevocation(jti=jti, user_id=user_id, expires_at=expires_at)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def purge_expired(db: Session) -> int:
    now = datetime.now(timezone.utc)
    rows = list(db.scalars(select(AuthRevocation).where(AuthRevocation.expires_at <= now)))
    for row in rows:
        db.delete(row)
    db.commit()
    return len(rows)
