"""domains, competencies, and typed edges

Revision ID: 0005_curriculum_graph
Revises: 0004_adult_acknowledgment
Create Date: 2026-09-23

"""

import sqlalchemy as sa
from alembic import op

revision: str = "0005_curriculum_graph"
down_revision: str | None = "0004_adult_acknowledgment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "domains",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_domains_key"),
    )
    op.create_table(
        "competencies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("domain_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_competencies_key"),
    )
    op.create_table(
        "competency_edges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("from_competency_id", sa.Uuid(), nullable=False),
        sa.Column("to_competency_id", sa.Uuid(), nullable=False),
        sa.Column("edge_type", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "from_competency_id <> to_competency_id",
            name="ck_competency_edges_no_self_loop",
        ),
        sa.CheckConstraint(
            "edge_type IN ('REQUIRES', 'RELATED')",
            name="ck_competency_edges_type",
        ),
        sa.ForeignKeyConstraint(
            ["from_competency_id"], ["competencies.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["to_competency_id"], ["competencies.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "from_competency_id",
            "to_competency_id",
            "edge_type",
            name="uq_competency_edges_endpoints",
        ),
    )


def downgrade() -> None:
    op.drop_table("competency_edges")
    op.drop_table("competencies")
    op.drop_table("domains")
