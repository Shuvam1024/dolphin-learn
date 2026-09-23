"""activity content fields: item ids, payloads, provisional, seven types

Revision ID: 0010_activity_content_fields
Revises: 0009_goal_domain_key
Create Date: 2026-09-23

"""

from __future__ import annotations

import json
import re

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_activity_content_fields"
down_revision: str | None = "0009_goal_domain_key"
branch_labels = None
depends_on = None

_CHOICE_LINE = re.compile(r"^([a-c])\)\s*(.*)$", re.IGNORECASE)


def _choices_from_prompt(prompt: str) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for raw in prompt.splitlines():
        line = raw.strip()
        match = _CHOICE_LINE.match(line)
        if match:
            found.append({"id": match.group(1).lower(), "label": match.group(2).strip() or line})
    return found


def upgrade() -> None:
    op.add_column(
        "lessons",
        sa.Column("provisional", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "lessons",
        sa.Column("source", sa.String(length=16), nullable=False, server_default="seed"),
    )

    op.add_column("activity_versions", sa.Column("item_id", sa.String(length=64), nullable=True))
    op.add_column("activity_versions", sa.Column("explanation", sa.Text(), nullable=True))
    op.add_column(
        "activity_versions",
        sa.Column("misconceptions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "activity_versions",
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "activity_versions",
        sa.Column("provisional", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "activity_versions",
        sa.Column("source", sa.String(length=16), nullable=False, server_default="seed"),
    )
    op.add_column(
        "activity_versions",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )

    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, version, activity_type, prompt FROM activity_versions")
    ).mappings()
    for row in rows:
        item_id = f"{row['activity_type']}-{row['version']}"
        choices = _choices_from_prompt(row["prompt"] or "")
        payload = {"choices": choices} if choices else {}
        bind.execute(
            sa.text(
                "UPDATE activity_versions SET item_id = :item_id, "
                "payload = CAST(:payload AS jsonb), reviewed_at = now() WHERE id = :id"
            ),
            {"item_id": item_id, "payload": json.dumps(payload), "id": row["id"]},
        )

    op.alter_column(
        "activity_versions",
        "item_id",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_activity_versions_item",
        "activity_versions",
        ["lesson_id", "item_id"],
    )

    op.drop_constraint("ck_activity_versions_type", "activity_versions", type_="check")
    op.create_check_constraint(
        "ck_activity_versions_type",
        "activity_versions",
        "activity_type IN ("
        "'reading', 'worked_example', 'objective', 'short_answer', "
        "'numeric', 'free_recall', 'reflection')",
    )
    op.create_check_constraint(
        "ck_activity_versions_source",
        "activity_versions",
        "source IN ('seed', 'learner', 'ai')",
    )
    op.create_check_constraint(
        "ck_lessons_source",
        "lessons",
        "source IN ('seed', 'learner', 'ai')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_lessons_source", "lessons", type_="check")
    op.drop_constraint("ck_activity_versions_source", "activity_versions", type_="check")
    op.drop_constraint("ck_activity_versions_type", "activity_versions", type_="check")
    op.create_check_constraint(
        "ck_activity_versions_type",
        "activity_versions",
        "activity_type IN ('reading', 'objective')",
    )
    op.drop_constraint("uq_activity_versions_item", "activity_versions", type_="unique")
    op.drop_column("activity_versions", "reviewed_at")
    op.drop_column("activity_versions", "source")
    op.drop_column("activity_versions", "provisional")
    op.drop_column("activity_versions", "payload")
    op.drop_column("activity_versions", "misconceptions")
    op.drop_column("activity_versions", "explanation")
    op.drop_column("activity_versions", "item_id")
    op.drop_column("lessons", "source")
    op.drop_column("lessons", "provisional")
