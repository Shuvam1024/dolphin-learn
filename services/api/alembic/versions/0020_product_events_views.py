"""product_events table and learning-dataset views

Revision ID: 0020_product_events_views
Revises: 0019_activity_difficulty
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020_product_events_views"
down_revision: Union[str, Sequence[str], None] = "0019_activity_difficulty"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("props", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_events_user_id", "product_events", ["user_id"])
    op.create_index("ix_product_events_name", "product_events", ["name"])

    op.execute(
        """
        CREATE OR REPLACE VIEW v_attempt_features AS
        SELECT
            a.id AS attempt_id,
            a.user_id,
            a.activity_version_id,
            av.difficulty AS item_difficulty,
            e.assistance,
            e.outcome,
            EXTRACT(EPOCH FROM (a.submitted_at - COALESCE(first_seen.first_at, a.submitted_at)))
                / 60.0 AS delay_since_exposure_minutes,
            COALESCE(active.active_minutes, 0) AS active_minutes,
            COALESCE(sel.selection_reason, 'unseen') AS selection_reason,
            a.submitted_at
        FROM attempts a
        JOIN activity_versions av ON av.id = a.activity_version_id
        LEFT JOIN evaluations e ON e.attempt_id = a.id
        LEFT JOIN LATERAL (
            SELECT MIN(se.created_at) AS first_at
            FROM session_events se
            JOIN sessions s ON s.id = se.session_id
            WHERE s.user_id = a.user_id
              AND (se.payload->>'activity_version_id') = a.activity_version_id::text
        ) first_seen ON TRUE
        LEFT JOIN LATERAL (
            SELECT SUM(
                CASE
                    WHEN (se.payload ? 'active_minutes')
                        THEN (se.payload->>'active_minutes')::numeric
                    WHEN (se.payload ? 'minutes')
                        THEN (se.payload->>'minutes')::numeric
                    ELSE 0
                END
            )::int AS active_minutes
            FROM session_events se
            WHERE a.session_id IS NOT NULL
              AND se.session_id = a.session_id
              AND se.event_type IN ('progress', 'activity_minutes', 'finish')
        ) active ON TRUE
        LEFT JOIN LATERAL (
            SELECT se.payload->>'selection_reason' AS selection_reason
            FROM session_events se
            WHERE a.session_id IS NOT NULL
              AND se.session_id = a.session_id
              AND (se.payload->>'activity_version_id') = a.activity_version_id::text
              AND se.payload ? 'selection_reason'
            ORDER BY se.created_at DESC
            LIMIT 1
        ) sel ON TRUE
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW v_review_outcomes AS
        SELECT
            re.id AS review_event_id,
            ri.user_id,
            ri.id AS review_item_id,
            ri.competency_id,
            ri.interval_days AS interval,
            re.outcome,
            EXTRACT(EPOCH FROM (re.created_at - ri.due_at)) / 60.0 AS delay_minutes,
            re.created_at
        FROM review_events re
        JOIN review_items ri ON ri.id = re.review_item_id
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_review_outcomes")
    op.execute("DROP VIEW IF EXISTS v_attempt_features")
    op.drop_index("ix_product_events_name", table_name="product_events")
    op.drop_index("ix_product_events_user_id", table_name="product_events")
    op.drop_table("product_events")
