"""Local user row keyed by the managed provider subject. No password column."""

import uuid
from datetime import datetime

from app.db import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, CheckConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    auth_subject: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LearnerProfile(Base):
    """1:1 preferences. Timezone is IANA. Accessibility flags are optional."""

    __tablename__ = "learner_profiles"
    __table_args__ = (
        CheckConstraint(
            "default_session_minutes >= 5 AND default_session_minutes <= 180",
            name="ck_learner_profiles_default_session_minutes",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    locale: Mapped[str] = mapped_column(String(35), nullable=False, default="en")
    a11y_prefs: Mapped[dict[str, bool]] = mapped_column(JSONB, nullable=False, default=dict)
    adult_acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ai_opt_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_session_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
