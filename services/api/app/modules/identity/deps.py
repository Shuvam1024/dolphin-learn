"""FastAPI dependency: bearer token → local user."""

from typing import Annotated

from app.db import get_db
from app.errors import ApiError
from app.modules.identity.models import User
from app.modules.identity.service import get_or_create_user
from app.modules.identity.tokens import decode_access_token
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

_bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError("unauthorized", "Authentication required", status_code=401)
    claims = decode_access_token(credentials.credentials, db=db)
    email = claims.get("email")
    user = get_or_create_user(
        db,
        auth_subject=str(claims["sub"]),
        email=email if isinstance(email, str) else None,
    )
    if user.deleted_at is not None:
        raise ApiError("unauthorized", "Account deleted", status_code=401)
    return user
