"""revoked access-token jtis for logout

Revision ID: 0022_auth_revocations
Revises: 0021_profile_session_minutes
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022_auth_revocations"
down_revision: Union[str, Sequence[str], None] = "0021_profile_session_minutes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_revocations",
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("jti"),
    )
    op.create_index("ix_auth_revocations_expires_at", "auth_revocations", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_auth_revocations_expires_at", table_name="auth_revocations")
    op.drop_table("auth_revocations")
