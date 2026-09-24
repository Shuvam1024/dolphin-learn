"""Diagnosable competencies and typed prerequisite edges. No lesson content yet."""

import uuid

from app.db import Base
from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

EDGE_REQUIRES = "REQUIRES"
EDGE_RELATED = "RELATED"


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)


class Competency(Base):
    __tablename__ = "competencies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("domains.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), nullable=True, index=True
    )


class CompetencyEdge(Base):
    """`from` requires `to` when edge_type is REQUIRES. Self-loops are rejected."""

    __tablename__ = "competency_edges"
    __table_args__ = (
        UniqueConstraint(
            "from_competency_id",
            "to_competency_id",
            "edge_type",
            name="uq_competency_edges_endpoints",
        ),
        CheckConstraint(
            "from_competency_id <> to_competency_id",
            name="ck_competency_edges_no_self_loop",
        ),
        CheckConstraint(
            "edge_type IN ('REQUIRES', 'RELATED')",
            name="ck_competency_edges_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    from_competency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    to_competency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    edge_type: Mapped[str] = mapped_column(String(32), nullable=False)
