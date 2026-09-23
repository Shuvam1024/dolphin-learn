"""Map an OIDC subject onto a local user row (create on first login)."""

from app.modules.identity.models import User
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
    return user
