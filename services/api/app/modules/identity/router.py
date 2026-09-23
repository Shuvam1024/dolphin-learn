"""Identity routes. Profile preferences arrive in a later step."""

import uuid

from app.errors import ApiError
from app.modules.identity.deps import current_user
from app.modules.identity.models import User
from app.modules.identity.tokens import dev_tokens_enabled, issue_dev_token
from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

router = APIRouter()


class DevTokenIn(BaseModel):
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


class MeOut(BaseModel):
    id: uuid.UUID
    auth_subject: str
    email: str | None


@router.post("/dev/token", response_model=DevTokenOut)
def dev_token(body: DevTokenIn) -> DevTokenOut:
    """Local stand-in for the OIDC token endpoint. Disabled in production."""
    if not dev_tokens_enabled():
        raise ApiError("not_found", "Not Found", status_code=404)
    return DevTokenOut(access_token=issue_dev_token(email=body.email))


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(current_user)) -> MeOut:
    return MeOut(id=user.id, auth_subject=user.auth_subject, email=user.email)
