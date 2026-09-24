"""users.deleted_at for account tombstones

Revision ID: 0023_users_deleted_at
Revises: 0022_auth_revocations
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023_users_deleted_at"
down_revision: Union[str, Sequence[str], None] = "0022_auth_revocations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "deleted_at")
