"""List seeded domains. A domain is curriculum data, not a second app."""

from app.db import get_db
from app.modules.curriculum.models import Domain
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/domains", tags=["domains"])


class DomainOut(BaseModel):
    key: str
    name: str


@router.get("", response_model=list[DomainOut])
def get_domains(db: Session = Depends(get_db)) -> list[DomainOut]:
    rows = db.scalars(select(Domain).order_by(Domain.key))
    return [DomainOut(key=row.key, name=row.name) for row in rows]
