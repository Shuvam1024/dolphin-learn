"""evaluation feedback_json for AI advisory notes

Revision ID: 0012_evaluation_feedback_json
Revises: 0011_ai_calls
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_evaluation_feedback_json"
down_revision: Union[str, Sequence[str], None] = "0011_ai_calls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluations",
        sa.Column("feedback_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluations", "feedback_json")
