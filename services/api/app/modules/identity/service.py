"""Map an OIDC subject onto a local user row (create on first login)."""

from datetime import datetime, timezone

from app.modules.identity.models import LearnerProfile, User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def get_or_create_user(db: Session, *, auth_subject: str, email: str | None) -> User:
    existing = db.scalar(select(User).where(User.auth_subject == auth_subject))
    if existing is not None:
        return existing
    user = User(auth_subject=auth_subject, email=email)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(User).where(User.auth_subject == auth_subject))
        if existing is None:
            raise
        return existing
    db.refresh(user)
    ensure_profile(db, user)
    return user


def ensure_profile(db: Session, user: User) -> LearnerProfile:
    profile = db.get(LearnerProfile, user.id)
    if profile is not None:
        return profile
    profile = LearnerProfile(user_id=user.id, timezone="UTC", locale="en", a11y_prefs={})
    db.add(profile)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        profile = db.get(LearnerProfile, user.id)
        if profile is None:
            raise
        return profile
    db.refresh(profile)
    return profile


def update_preferences(
    db: Session,
    user: User,
    *,
    display_name: str | None,
    timezone: str | None,
    locale: str | None,
    a11y_prefs: dict[str, bool] | None,
    set_display_name: bool,
    default_session_minutes: int | None = None,
    ai_opt_out: bool | None = None,
) -> LearnerProfile:
    """Update only fields the caller sent. Always the authenticated user."""
    profile = ensure_profile(db, user)
    if set_display_name:
        profile.display_name = display_name
    if timezone is not None:
        profile.timezone = timezone
    if locale is not None:
        profile.locale = locale
    if a11y_prefs is not None:
        profile.a11y_prefs = a11y_prefs
    if default_session_minutes is not None:
        profile.default_session_minutes = int(default_session_minutes)
    if ai_opt_out is not None:
        profile.ai_opt_out = bool(ai_opt_out)
    db.commit()
    db.refresh(profile)
    return profile


def acknowledge_adult(db: Session, user: User) -> LearnerProfile:
    """Record the 18+ acknowledgment once. Later calls keep the original time."""
    profile = ensure_profile(db, user)
    if profile.adult_acknowledged_at is None:
        profile.adult_acknowledged_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(profile)
    return profile
