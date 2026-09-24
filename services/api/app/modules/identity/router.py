"""Identity routes: session subject and owner-scoped preferences."""

import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.db import get_db
from app.errors import ApiError
from app.modules.identity.deps import current_user
from app.modules.identity.models import LearnerProfile, User
from app.modules.identity.service import acknowledge_adult, ensure_profile, update_preferences
from app.modules.identity.tokens import dev_tokens_enabled, issue_dev_token, revoke_access_token
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

router = APIRouter()

_LOCALE = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")


class DevTokenIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if "@" not in cleaned or " " in cleaned or cleaned.startswith("@") or cleaned.endswith("@"):
            raise ValueError("email must look like an email address")
        return cleaned


class DevTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class A11yPrefs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reduced_motion: bool = False
    larger_text: bool = False


class ProfileOut(BaseModel):
    display_name: str | None
    timezone: str
    locale: str
    a11y_prefs: A11yPrefs
    adult_acknowledged_at: datetime | None
    default_session_minutes: int = 25
    ai_opt_out: bool = False
    use_tutor: bool = True


class MeOut(BaseModel):
    id: uuid.UUID
    auth_subject: str
    email: str | None
    profile: ProfileOut
    ai_enabled: bool = False


class PreferencesIn(BaseModel):
    """Only the authenticated learner is updated. Extra ids are rejected."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = None
    timezone: str | None = None
    locale: str | None = None
    a11y_prefs: A11yPrefs | None = None
    default_session_minutes: int | None = None
    ai_opt_out: bool | None = None
    use_tutor: bool | None = None

    @field_validator("display_name")
    @classmethod
    def _name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if len(cleaned) > 80:
            raise ValueError("display name must be 80 characters or fewer")
        return cleaned

    @field_validator("timezone")
    @classmethod
    def _zone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be an IANA name") from exc
        return value

    @field_validator("locale")
    @classmethod
    def _locale(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _LOCALE.match(value):
            raise ValueError("locale must look like en or en-US")
        return value

    @field_validator("default_session_minutes")
    @classmethod
    def _minutes(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 5 or value > 180:
            raise ValueError("default_session_minutes must be between 5 and 180")
        return value


def _profile_out(profile: LearnerProfile) -> ProfileOut:
    raw = profile.a11y_prefs or {}
    return ProfileOut(
        display_name=profile.display_name,
        timezone=profile.timezone,
        locale=profile.locale,
        a11y_prefs=A11yPrefs(
            reduced_motion=bool(raw.get("reduced_motion", False)),
            larger_text=bool(raw.get("larger_text", False)),
        ),
        adult_acknowledged_at=profile.adult_acknowledged_at,
        default_session_minutes=int(profile.default_session_minutes or 25),
        ai_opt_out=bool(profile.ai_opt_out),
        use_tutor=not bool(profile.ai_opt_out),
    )


def _me(user: User, profile: LearnerProfile, db: Session) -> MeOut:
    from app.modules.ai_gateway.service import is_enabled

    return MeOut(
        id=user.id,
        auth_subject=user.auth_subject,
        email=user.email,
        profile=_profile_out(profile),
        ai_enabled=is_enabled(db, user),
    )


@router.post("/dev/token", response_model=DevTokenOut)
def dev_token(body: DevTokenIn) -> DevTokenOut:
    """Local stand-in for the OIDC token endpoint. Disabled in production."""
    if not dev_tokens_enabled():
        raise ApiError("not_found", "Not Found", status_code=404)
    return DevTokenOut(access_token=issue_dev_token(email=body.email))


@router.get("/me", response_model=MeOut)
def me(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> MeOut:
    return _me(user, ensure_profile(db, user), db)


@router.patch("/me/preferences", response_model=MeOut)
def patch_preferences(
    body: PreferencesIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> MeOut:
    sent = body.model_fields_set
    ai_opt_out = body.ai_opt_out
    if "use_tutor" in sent and body.use_tutor is not None:
        ai_opt_out = not body.use_tutor
    profile = update_preferences(
        db,
        user,
        display_name=body.display_name,
        timezone=body.timezone,
        locale=body.locale,
        a11y_prefs=body.a11y_prefs.model_dump() if body.a11y_prefs is not None else None,
        set_display_name="display_name" in sent,
        default_session_minutes=body.default_session_minutes,
        ai_opt_out=ai_opt_out,
    )
    return _me(user, profile, db)


@router.post("/me/adult-acknowledgment", response_model=MeOut)
def adult_acknowledgment(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> MeOut:
    """Record that this adult learner accepted the 18+ enrollment notice."""
    return _me(user, acknowledge_adult(db, user), db)


class RevokeOut(BaseModel):
    revoked: bool = True


@router.post("/auth/revoke", response_model=RevokeOut)
def revoke_session(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> RevokeOut:
    """Revoke the bearer access token on logout. Managed auth only — no credentials stored."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError("unauthorized", "Authentication required", status_code=401)
    token = authorization.split(" ", 1)[1].strip()
    user: User | None = None
    try:
        from app.modules.identity.tokens import decode_access_token

        claims = decode_access_token(token, db=None)
        email = claims.get("email")
        from app.modules.identity.service import get_or_create_user

        user = get_or_create_user(
            db,
            auth_subject=str(claims["sub"]),
            email=email if isinstance(email, str) else None,
        )
    except ApiError:
        user = None
    revoke_access_token(db, token, user_id=user.id if user else None)
    return RevokeOut(revoked=True)
